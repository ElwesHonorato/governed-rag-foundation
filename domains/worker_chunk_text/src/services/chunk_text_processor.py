import json
from typing import Any, ClassVar

from chunking.domain.central_text_splitter import CentralTextSplitter
from configs.chunking_scaffold import ChunkingStage, ChunkingStages
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.provenance import build_id, chunk_params_hash, sha256_hex
from pipeline_common.stages_contracts import (
    ArtifactPayload,
    BaseProcessor,
    ParsedTextPayload,
)

from contracts.contracts import (
    ChunkArtifactPayload,
    ChunkArtifactRecord,
    ChunkBuildContext,
    ChunkingExecutionResult,
    ProcessResult,
    ResolvedChunkContent,
    SourceDocumentMetadata,
)


class ChunkTextProcessor(BaseProcessor):
    """Transform processed document rows into persisted chunk artifacts.

    The processor handles the full chunking pipeline for a single payload:
    normalize source text into chunk records, write chunk artifacts, and return
    metadata required by downstream manifest assembly.
    """

    VERSION: ClassVar[str] = "1.0.0"
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
        processed_payload: ArtifactPayload[ParsedTextPayload],
        source_uri: str,
        run_id: str,
        stages: ChunkingStages,
    ) -> ProcessResult:
        return self.process_stage(
            processed_payload=processed_payload,
            source_uri=source_uri,
            run_id=run_id,
            stages=stages,
        )

    def process_stage(
        self,
        *,
        processed_payload: ArtifactPayload[ParsedTextPayload],
        source_uri: str,
        run_id: str,
        stages: ChunkingStages,
    ) -> ProcessResult:
        """Run the golden path once: stage-chain split and persist chunk artifacts."""
        serialized_stages = stages.to_serializable_dict()
        source_text = processed_payload.content.text
        source_metadata = processed_payload.source_metadata
        input_content_hash = source_metadata.source_content_hash
        chunk_build_context = ChunkBuildContext(
            chunk_params_hash=chunk_params_hash(serialized_stages),
            chunking_params=serialized_stages,
        )
        documents = self._process_stages(
            source_text=source_text,
            stages=stages.stages,
        )

        records = self._build_chunk_records(
            documents=documents,
            run_id=run_id,
            source_metadata=source_metadata,
            source_uri=source_uri,
            input_content_hash=input_content_hash,
            chunk_build_context=chunk_build_context,
        )

        written, chunk_entries = self._write_chunk_records(records)

        return ProcessResult(
            run_id=run_id,
            source_metadata=source_metadata,
            source_uri=source_uri,
            input_content_hash=input_content_hash,
            processor=self._build_processor_metadata(),
            result=ChunkingExecutionResult(
                chunk_count_expected=len(records),
                chunk_count_written=written,
                chunk_entries=chunk_entries,
                chunking_params=chunk_build_context.chunking_params,
            ),
        )

    def _build_chunk_records(
        self,
        documents: list[Any],
        run_id: str,
        source_metadata: SourceDocumentMetadata,
        source_uri: str,
        input_content_hash: str,
        chunk_build_context: ChunkBuildContext,
    ) -> list[ChunkArtifactRecord]:
        records: list[ChunkArtifactRecord] = []
        for chunk_index, chunk_document in enumerate(documents):
            resolved_content: ResolvedChunkContent = self._resolve_chunk_content(
                chunk_document=chunk_document,
                source_uri=source_uri,
                input_content_hash=input_content_hash,
                chunk_build_context=chunk_build_context,
            )

            chunk_object_key = self._chunk_object_key(
                doc_id=source_metadata.doc_id,
                run_id=run_id,
                chunk_id=resolved_content.chunk_id,
            )

            payload: ChunkArtifactPayload = ChunkArtifactPayload(
                source_metadata=source_metadata,
                processor_metadata=self._build_processor_metadata(),
                content=ParsedTextPayload(title="", text=resolved_content.chunk_text),
            )
            chunk_record: ChunkArtifactRecord = ChunkArtifactRecord(
                payload=payload,
                destination_key=chunk_object_key,
                chunk_id=resolved_content.chunk_id,
                chunk_index=chunk_index,
                chunk_text_hash=resolved_content.chunk_text_hash,
            )
            records.append(chunk_record)

        return records

    def _resolve_chunk_content(
        self,
        *,
        chunk_document: Any,
        source_uri: str,
        input_content_hash: str,
        chunk_build_context: ChunkBuildContext,
    ) -> ResolvedChunkContent:
        chunk_text = str(chunk_document.page_content)
        offsets_start = int(chunk_document.metadata.get("start_index", 0))
        offsets_end = offsets_start + len(chunk_text)
        return ResolvedChunkContent(
            chunk_id=build_id(
                source_dataset_urn=source_uri,
                source_content_hash_value=input_content_hash,
                chunker_version=self.VERSION,
                chunk_params_hash_value=chunk_build_context.chunk_params_hash,
                offsets_start=offsets_start,
                offsets_end=offsets_end,
            ),
            chunk_text=chunk_text,
            offsets_start=offsets_start,
            offsets_end=offsets_end,
            chunk_text_hash=sha256_hex(chunk_text),
        )

    def _write_chunk_records(
        self,
        records: list[ChunkArtifactRecord],
    ) -> tuple[int, list[dict[str, Any]]]:
        written = 0
        chunk_entries: list[dict[str, Any]] = []

        for chunk_record in records:
            chunk_entries.append(self._build_chunk_manifest_entry(chunk_record))
            self._write_chunk_object(chunk_record)
            written += 1

        return written, chunk_entries

    def _build_chunk_manifest_entry(
        self,
        chunk_record: ChunkArtifactRecord,
    ) -> dict[str, Any]:
        return {
            "chunk_id": chunk_record.chunk_id,
            "chunk_index": chunk_record.chunk_index,
            "chunk_hash": chunk_record.chunk_text_hash,
            "path": chunk_record.destination_key,
        }

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
            )
        return docs

    def _apply_stage(
        self,
        *,
        splitter: CentralTextSplitter,
        docs: list[Any],
    ) -> list[Any]:
        if self._docs_are_documents(docs):
            return splitter.split_documents(documents=docs)
        texts = [str(item) for item in docs]
        return splitter.create_documents(texts=texts)

    def _docs_are_documents(self, docs: list[Any]) -> bool:
        return bool(docs) and hasattr(docs[0], "page_content")

    def _chunk_object_key(self, doc_id: str, run_id: str, chunk_id: str) -> str:
        return (
            f"{self.output_prefix.rstrip('/')}/"
            f"{self.CHUNKS_DIR}/{doc_id}/run={run_id}/chunk={chunk_id}.json"
        )
