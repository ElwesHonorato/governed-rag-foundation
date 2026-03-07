import json
from dataclasses import dataclass
from typing import ClassVar

from chunking.domain.central_text_splitter import CentralTextSplitter
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.provenance import build_chunk_id, chunk_params_hash, sha256_hex
from pipeline_common.stages_contracts import ChunkArtifactPayload, ChunkDocumentMetadata, ProcessedDocumentPayload

from contracts.chunk_manifest import (
    ChunkerConfig,
    ChunkManifest,
    ChunkManifestEntry,
    ChunkManifestLineage,
    ChunkManifestOutput,
    ChunkManifestProcessing,
)
from contracts.contracts import ChunkingParamsContract


@dataclass(frozen=True)
class ChunkArtifactRecord:
    payload: ChunkArtifactPayload
    destination_key: str


class ChunkTextProcessor:
    """Transform processed document rows into persisted chunk artifacts.

    The processor handles the full chunking pipeline for a single payload:
    normalize source text into chunk records, write chunk artifacts, and write
    a manifest describing the output of the run.
    """

    CHUNKER_VERSION: ClassVar[str] = "1.0.0"
    STAGE_NAME: ClassVar[str] = "chunk_text"
    CHUNKS_DIR: ClassVar[str] = "chunks"
    CHUNKS_MANIFEST_DIR: ClassVar[str] = "chunks_manifest"
    MANIFEST_FILE_NAME: ClassVar[str] = "manifest.json"

    def __init__(
        self,
        object_storage: ObjectStorageGateway,
        storage_bucket: str,
        output_prefix: str,
        manifest_prefix: str,
        chunking_params: ChunkingParamsContract,
    ) -> None:
        self.object_storage = object_storage
        self.storage_bucket = storage_bucket
        self.output_prefix = output_prefix
        self.manifest_prefix = manifest_prefix
        self._chunking_params = chunking_params
        self._splitter = CentralTextSplitter(
            strategy=chunking_params.strategy,
            chunk_size=chunking_params.chunk_size,
            chunk_overlap=chunking_params.chunk_overlap,
            add_start_index=chunking_params.add_start_index,
        )

    def process(
        self,
        processed_payload: ProcessedDocumentPayload,
        source_uri: str,
        chunking_run_id: str,
    ) -> int:
        (
            source_text,
            chunk_document_metadata,
            resolved_chunk_params_hash,
            parser_version,
            content_type,
        ) = self._initialize_chunking_context(
            payload=processed_payload,
            source_uri=source_uri,
            chunking_run_id=chunking_run_id,
        )

        records = self._build_chunk_records(
            source_text=source_text,
            chunk_document_metadata=chunk_document_metadata,
            chunk_params_hash_value=resolved_chunk_params_hash,
        )

        written, chunk_entries = self._write_chunk_records(records)

        manifest = self._build_manifest(
            chunk_document_metadata=chunk_document_metadata,
            parser_version=parser_version,
            content_type=content_type,
            written=written,
            chunk_count_expected=len(records),
            chunk_entries=chunk_entries,
        )
        self._write_manifest(
            manifest=manifest,
            doc_id=chunk_document_metadata.doc_id,
            run_id=chunk_document_metadata.chunking_run_id,
        )

        return written

    def _initialize_chunking_context(
        self,
        payload: ProcessedDocumentPayload,
        source_uri: str,
        chunking_run_id: str,
    ) -> tuple[str, ChunkDocumentMetadata, str, str, str]:
        source_text = str(payload.parsed["text"])
        source_content_hash = sha256_hex(source_text)
        resolved_chunk_params_hash = chunk_params_hash(self._chunking_params.to_dict())
        parser_version = str(payload.parsed.get("parser_version", "unknown"))
        content_type = str(payload.parsed.get("content_type", "text/html"))

        chunk_document_metadata = ChunkDocumentMetadata(
            doc_id=payload.metadata.doc_id,
            timestamp=payload.metadata.timestamp,
            security_clearance=payload.metadata.security_clearance,
            source_dataset_urn=source_uri,
            source_s3_uri=source_uri,
            source_content_hash=source_content_hash,
            chunking_run_id=chunking_run_id,
            source_type="html",
        )

        return (
            source_text,
            chunk_document_metadata,
            resolved_chunk_params_hash,
            parser_version,
            content_type,
        )

    def _build_chunk_records(
        self,
        source_text: str,
        chunk_document_metadata: ChunkDocumentMetadata,
        chunk_params_hash_value: str,
    ) -> list[ChunkArtifactRecord]:
        documents = self._splitter.create_documents(
            [source_text],
            metadatas=[chunk_document_metadata.to_dict()],
        )

        records: list[ChunkArtifactRecord] = []
        for chunk_index, chunk_document in enumerate(documents):
            chunk_text_value = str(chunk_document.page_content)
            offsets_start = int(chunk_document.metadata.get("start_index", 0))
            offsets_end = offsets_start + len(chunk_text_value)
            resolved_chunk_text_hash = sha256_hex(chunk_text_value)

            resolved_chunk_id = build_chunk_id(
                source_dataset_urn=chunk_document_metadata.source_dataset_urn,
                source_content_hash_value=chunk_document_metadata.source_content_hash,
                chunker_name=self.__class__.__name__,
                chunker_version=self.CHUNKER_VERSION,
                chunk_params_hash_value=chunk_params_hash_value,
                offsets_start=offsets_start,
                offsets_end=offsets_end,
            )

            destination_key = self._chunk_object_key(
                doc_id=chunk_document_metadata.doc_id,
                run_id=chunk_document_metadata.chunking_run_id,
                chunk_id=resolved_chunk_id,
            )

            records.append(
                ChunkArtifactRecord(
                    payload=ChunkArtifactPayload(
                        doc_id=chunk_document_metadata.doc_id,
                        chunk_id=resolved_chunk_id,
                        chunk_index=chunk_index,
                        chunk_text=chunk_text_value,
                        source_type=chunk_document_metadata.source_type,
                        timestamp=chunk_document_metadata.timestamp,
                        security_clearance=chunk_document_metadata.security_clearance,
                        source_dataset_urn=chunk_document_metadata.source_dataset_urn,
                        source_s3_uri=chunk_document_metadata.source_s3_uri,
                        source_content_hash=chunk_document_metadata.source_content_hash,
                        offsets_start=offsets_start,
                        offsets_end=offsets_end,
                        breadcrumb=f"chunk[{chunk_index}]",
                        chunking_run_id=chunk_document_metadata.chunking_run_id,
                        chunk_text_hash=resolved_chunk_text_hash,
                        chunker_name=self.__class__.__name__,
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

    def _build_manifest(
        self,
        chunk_document_metadata: ChunkDocumentMetadata,
        parser_version: str,
        content_type: str,
        written: int,
        chunk_count_expected: int,
        chunk_entries: list[ChunkManifestEntry],
    ) -> ChunkManifest:
        source_uri = chunk_document_metadata.source_s3_uri

        lineage = ChunkManifestLineage(
            source_asset_id=source_uri,
            source_hash=sha256_hex(source_uri),
            content_type=content_type,
            document_hash=chunk_document_metadata.source_content_hash,
            parser_version=parser_version,
        )

        processing = ChunkManifestProcessing(
            run_id=chunk_document_metadata.chunking_run_id,
            stage=self.STAGE_NAME,
            timestamp=chunk_document_metadata.timestamp,
            chunker_version=self.CHUNKER_VERSION,
            run_status="complete" if written == chunk_count_expected else "partial",
            chunker=ChunkerConfig(
                strategy=self._chunking_params.strategy,
                chunk_size=self._chunking_params.chunk_size,
                chunk_overlap=self._chunking_params.chunk_overlap,
            ),
        )

        output = ChunkManifestOutput(
            chunk_count_expected=chunk_count_expected,
            chunk_count_written=written,
        )

        return ChunkManifest.build(
            doc_id=chunk_document_metadata.doc_id,
            lineage=lineage,
            processing=processing,
            output=output,
            chunks=chunk_entries,
        )

    def _write_manifest(
        self,
        manifest: ChunkManifest,
        doc_id: str,
        run_id: str,
    ) -> None:
        self.object_storage.write_object(
            self.storage_bucket,
            self._manifest_object_key(doc_id=doc_id, run_id=run_id),
            json.dumps(
                manifest.to_dict(),
                sort_keys=True,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("utf-8"),
            content_type="application/json",
        )

    def _chunk_object_key(self, doc_id: str, run_id: str, chunk_id: str) -> str:
        return (
            f"{self.output_prefix.rstrip('/')}/"
            f"{self.CHUNKS_DIR}/{doc_id}/run={run_id}/chunk={chunk_id}.json"
        )

    def _manifest_object_key(self, doc_id: str, run_id: str) -> str:
        return (
            f"{self.manifest_prefix.rstrip('/')}/"
            f"{self.CHUNKS_MANIFEST_DIR}/{doc_id}/run={run_id}/"
            f"{self.MANIFEST_FILE_NAME}"
        )
