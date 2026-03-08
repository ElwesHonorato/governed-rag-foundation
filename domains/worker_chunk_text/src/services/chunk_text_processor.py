import json
from dataclasses import dataclass
from typing import Any, ClassVar

from chunking.domain.central_text_splitter import CentralTextSplitter
from configs.chunking_scaffold import ChunkingStage, ChunkingStages
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.provenance import build_chunk_id, chunk_params_hash, sha256_hex
from pipeline_common.stages_contracts import (
    ChunkArtifactPayload,
    ChunkDocumentMetadata,
    ProcessedDocumentPayload,
    ProcessorMetadata,
)

from contracts.chunk_manifest import ChunkManifestEntry


@dataclass(frozen=True)
class ChunkArtifactRecord:
    payload: ChunkArtifactPayload
    destination_key: str


@dataclass(frozen=True)
class ChunkProcessResult:
    chunk_document_metadata: ChunkDocumentMetadata
    processor_metadata: ProcessorMetadata
    chunk_count_expected: int
    chunk_count_written: int
    chunk_entries: list[ChunkManifestEntry]
    chunking_params: dict[str, Any]
    stage_name: str


class ChunkTextProcessor:
    """Transform processed document rows into persisted chunk artifacts.

    The processor handles the full chunking pipeline for a single payload:
    normalize source text into chunk records, write chunk artifacts, and return
    metadata required by downstream manifest assembly.
    """

    CHUNKER_VERSION: ClassVar[str] = "1.0.0"
    STAGE_NAME: ClassVar[str] = "chunk_text"
    CHUNKS_DIR: ClassVar[str] = "chunks"

    def __init__(
        self,
        object_storage: ObjectStorageGateway,
        storage_bucket: str,
        output_prefix: str,
    ) -> None:
        self.object_storage = object_storage
        self.storage_bucket = storage_bucket
        self.output_prefix = output_prefix

    def process(
        self,
        processed_payload: ProcessedDocumentPayload,
        source_uri: str,
        run_id: str,
        stages: ChunkingStages,
    ) -> ChunkProcessResult:
        return self.process_stage(
            processed_payload=processed_payload,
            source_uri=source_uri,
            run_id=run_id,
            stages=stages,
        )

    def process_stage(
        self,
        *,
        processed_payload: ProcessedDocumentPayload,
        source_uri: str,
        run_id: str,
        stages: ChunkingStages,
    ) -> ChunkProcessResult:
        """Run the golden path once: stage-chain split and persist chunk artifacts."""
        serialized_stages = stages.to_serializable_dict()
        source_text = processed_payload.parsed.text
        chunk_document_metadata = ChunkDocumentMetadata(
            source_metadata=processed_payload.metadata,
            input_dataset_urn=source_uri,
            input_content_hash=sha256_hex(source_text),
            run_id=run_id,
        )
        documents = self._process_stages(
            source_text=source_text,
            stages=stages.stages,
            chunk_document_metadata=chunk_document_metadata,
        )

        records = self._build_chunk_records(
            documents=documents,
            chunk_document_metadata=chunk_document_metadata,
            chunk_params_hash_value=chunk_params_hash(serialized_stages),
        )

        written, chunk_entries = self._write_chunk_records(records)

        return ChunkProcessResult(
            chunk_document_metadata=chunk_document_metadata,
            processor_metadata=processed_payload.processor_metadata,
            chunk_count_expected=len(records),
            chunk_count_written=written,
            chunk_entries=chunk_entries,
            chunking_params=serialized_stages,
            stage_name=self.STAGE_NAME,
        )

    def _build_chunk_records(
        self,
        documents: list[Any],
        chunk_document_metadata: ChunkDocumentMetadata,
        chunk_params_hash_value: str,
    ) -> list[ChunkArtifactRecord]:
        records: list[ChunkArtifactRecord] = []
        for chunk_index, chunk_document in enumerate(documents):
            chunk_text_value = str(chunk_document.page_content)
            offsets_start = int(chunk_document.metadata.get("start_index", 0))
            offsets_end = offsets_start + len(chunk_text_value)
            resolved_chunk_text_hash = sha256_hex(chunk_text_value)

            resolved_chunk_id = build_chunk_id(
                source_dataset_urn=chunk_document_metadata.input_dataset_urn,
                source_content_hash_value=chunk_document_metadata.input_content_hash,
                chunker_version=self.CHUNKER_VERSION,
                chunk_params_hash_value=chunk_params_hash_value,
                offsets_start=offsets_start,
                offsets_end=offsets_end,
            )

            destination_key = self._chunk_object_key(
                doc_id=chunk_document_metadata.source_metadata.doc_id,
                run_id=chunk_document_metadata.run_id,
                chunk_id=resolved_chunk_id,
            )

            records.append(
                ChunkArtifactRecord(
                    payload=ChunkArtifactPayload(
                        doc_id=chunk_document_metadata.source_metadata.doc_id,
                        chunk_id=resolved_chunk_id,
                        chunk_index=chunk_index,
                        chunk_text=chunk_text_value,
                        source_type=chunk_document_metadata.source_metadata.source_type,
                        timestamp=chunk_document_metadata.source_metadata.timestamp,
                        security_clearance=chunk_document_metadata.source_metadata.security_clearance,
                        source_dataset_urn=chunk_document_metadata.input_dataset_urn,
                        source_s3_uri=chunk_document_metadata.input_dataset_urn,
                        source_content_hash=chunk_document_metadata.input_content_hash,
                        offsets_start=offsets_start,
                        offsets_end=offsets_end,
                        breadcrumb=f"chunk[{chunk_index}]",
                        run_id=chunk_document_metadata.run_id,
                        chunk_text_hash=resolved_chunk_text_hash,
                        chunker_version=self.CHUNKER_VERSION,
                        chunk_params_hash=chunk_params_hash_value,
                    ),
                    destination_key=destination_key,
                )
            )

        return records

    def _write_chunk_records(
        self,
        records: list[ChunkArtifactRecord],
    ) -> tuple[int, list[ChunkManifestEntry]]:
        written = 0
        chunk_entries: list[ChunkManifestEntry] = []

        for chunk_record in records:
            chunk_entries.append(self._build_chunk_manifest_entry(chunk_record))
            self._write_chunk_object(chunk_record)
            written += 1

        return written, chunk_entries

    def _build_chunk_manifest_entry(
        self,
        chunk_record: ChunkArtifactRecord,
    ) -> ChunkManifestEntry:
        return ChunkManifestEntry(
            chunk_id=chunk_record.payload.chunk_id,
            chunk_index=chunk_record.payload.chunk_index,
            chunk_hash=chunk_record.payload.chunk_text_hash,
            path=chunk_record.destination_key,
        )

    def _write_chunk_object(self, chunk_record: ChunkArtifactRecord) -> None:
        self.object_storage.write_object(
            self.storage_bucket,
            chunk_record.destination_key,
            json.dumps(
                {
                    **chunk_record.payload.to_dict(),
                    "destination_key": chunk_record.destination_key,
                },
                sort_keys=True,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("utf-8"),
            content_type="application/json",
        )

    def _process_stages(
        self,
        *,
        source_text: str,
        stages: list[ChunkingStage],
        chunk_document_metadata: ChunkDocumentMetadata,
    ) -> list[Any]:
        """Apply each LangChain stage sequentially, feeding one stage output into the next.

        Starts from raw source text, then repeatedly splits either:
        - raw text inputs (via `create_documents`), or
        - document inputs from a previous stage (via `split_documents`).
        Returns the final document list.
        """
        docs: list[Any] = [source_text]

        for stage in stages:
            splitter = CentralTextSplitter(stage=stage)
            docs = self._apply_stage(
                splitter=splitter,
                docs=docs,
                chunk_document_metadata=chunk_document_metadata,
            )
        return docs

    def _apply_stage(
        self,
        *,
        splitter: CentralTextSplitter,
        docs: list[Any],
        chunk_document_metadata: ChunkDocumentMetadata,
    ) -> list[Any]:
        if self._docs_are_documents(docs):
            return splitter.split_documents(documents=docs)
        texts = [str(item) for item in docs]
        return splitter.create_documents(
            texts=texts,
            metadatas=[dict(chunk_document_metadata.to_dict()) for _ in texts],
        )

    def _docs_are_documents(self, docs: list[Any]) -> bool:
        return bool(docs) and hasattr(docs[0], "page_content")

    def _chunk_object_key(self, doc_id: str, run_id: str, chunk_id: str) -> str:
        return (
            f"{self.output_prefix.rstrip('/')}/"
            f"{self.CHUNKS_DIR}/{doc_id}/run={run_id}/chunk={chunk_id}.json"
        )
