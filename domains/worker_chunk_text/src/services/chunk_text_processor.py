import json
from typing import Any, ClassVar

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.provenance import (
    build_chunk_id,
    sha256_hex,
)
from pipeline_common.provenance import chunk_params_hash
from pipeline_common.stages_contracts import ChunkDocumentMetadata, ProcessedDocumentPayload
from contracts.chunk_manifest import (
    ChunkerConfig,
    ChunkManifest,
    ChunkManifestEntry,
    ChunkManifestLineage,
    ChunkManifestOutput,
    ChunkManifestProcessing,
)
from contracts.contracts import ChunkingParamsContract


class ChunkTextProcessor:
    """Transform processed document rows into persisted chunk artifacts.

    The processor handles the full chunking pipeline for a single dataframe batch:
    normalize/expand rows into chunk rows, materialize rows into Python records,
    write chunk artifact objects.
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
        """Initialize processor dependencies and storage routing configuration.

        Args:
            object_storage: Gateway used to read/write chunk artifacts in object storage.
            storage_bucket: Bucket name where chunk artifacts are persisted.
            output_prefix: Key prefix under the bucket for chunk artifacts.
            manifest_prefix: Key prefix under the bucket for chunk manifests.

        Returns:
            None.
        """
        self.object_storage = object_storage
        self.storage_bucket = storage_bucket
        self.output_prefix = output_prefix
        self.manifest_prefix = manifest_prefix
        self._chunking_params = chunking_params
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunking_params.chunk_size,
            chunk_overlap=chunking_params.chunk_overlap,
            add_start_index=chunking_params.add_start_index,
        )
        self.chunk_entries = []
        self.written = 0
        self.chunk_count_expected = 0

    def process(
        self,
        processed_payload: ProcessedDocumentPayload,
        source_uri: str,
        chunking_run_id: str,
    ) -> int:
        """Run chunk expansion and persistence for a processed-document payload.

        Args:
            processed_payload: Parsed processed-document payload object.
            source_uri: Canonical source dataset URI.
            chunking_run_id: Run identifier for provenance stamping.

        Returns:
            Number of new chunk artifact objects created.

        Side Effects:
            Writes chunk artifact objects to object storage (if missing).
        """
        records = self._build_chunk_records_from_payload(
            processed_payload,
            source_uri=source_uri,
            chunking_run_id=chunking_run_id,
        )
        return self._write_chunk_records(records)

    def _build_chunk_records_from_payload(
        self,
        payload: ProcessedDocumentPayload,
        source_uri: str,
        chunking_run_id: str,
    ) -> list[dict[str, Any]]:
        """Build chunk record dictionaries from processed-document payload.

        Args:
            payload: Processed-document payload JSON.
            source_uri: Canonical source dataset URI.
            chunking_run_id: Run identifier for provenance stamping.

        Returns:
            A list of chunk record dictionaries for artifact persistence.
        """
        source_text, resolved_chunk_params_hash = self._initialize_chunking_context(
            payload=payload,
            source_uri=source_uri,
            chunking_run_id=chunking_run_id,
        )
        documents = self._splitter.create_documents([source_text], metadatas=[self.chunk_document_metadata.to_dict()])

        records: list[dict[str, Any]] = []
        for chunk_index, chunk_document in enumerate(documents):
            chunk_text_value = str(chunk_document.page_content)
            offsets_start = int(chunk_document.metadata.get("start_index", 0))
            offsets_end = offsets_start + len(chunk_text_value)
            resolved_chunk_text_hash = sha256_hex(chunk_text_value)
            resolved_chunk_id = build_chunk_id(
                source_dataset_urn=self.chunk_document_metadata.source_dataset_urn,
                source_content_hash_value=self.chunk_document_metadata.source_content_hash,
                chunker_name=self.__class__.__name__,
                chunker_version=self.CHUNKER_VERSION,
                chunk_params_hash_value=resolved_chunk_params_hash,
                offsets_start=offsets_start,
                offsets_end=offsets_end,
            )
            destination_key = self._chunk_object_key(self.chunk_document_metadata.doc_id, resolved_chunk_id)
            records.append(
                {
                    "doc_id": self.chunk_document_metadata.doc_id,
                    "chunk_id": resolved_chunk_id,
                    "chunk_index": chunk_index,
                    "chunk_text": chunk_text_value,
                    "source_type": self.chunk_document_metadata.source_type,
                    "timestamp": self.chunk_document_metadata.timestamp,
                    "security_clearance": self.chunk_document_metadata.security_clearance,
                    "source_dataset_urn": self.chunk_document_metadata.source_dataset_urn,
                    "source_s3_uri": self.chunk_document_metadata.source_s3_uri,
                    "source_content_hash": self.chunk_document_metadata.source_content_hash,
                    "offsets_start": offsets_start,
                    "offsets_end": offsets_end,
                    "breadcrumb": f"chunk[{chunk_index}]",
                    "chunking_run_id": self.chunk_document_metadata.chunking_run_id,
                    "chunk_text_hash": resolved_chunk_text_hash,
                    "chunker_name": self.__class__.__name__,
                    "chunker_version": self.CHUNKER_VERSION,
                    "chunk_params_hash": resolved_chunk_params_hash,
                    "destination_key": destination_key,
                }
            )
        return records

    def _initialize_chunking_context(
        self,
        payload: ProcessedDocumentPayload,
        source_uri: str,
        chunking_run_id: str,
    ) -> tuple[str, str]:
        source_text = str(payload.parsed["text"])
        source_content_hash = sha256_hex(source_text)
        resolved_chunk_params_hash = chunk_params_hash(self._chunking_params.to_dict())
        self._manifest_parser_version = payload.parsed.get("parser_version", "unknown")
        self._manifest_content_type = payload.parsed.get("content_type", "text/html")
        self.chunk_document_metadata = ChunkDocumentMetadata(
            doc_id=payload.metadata.doc_id,
            timestamp=payload.metadata.timestamp,
            security_clearance=payload.metadata.security_clearance,
            source_dataset_urn=source_uri,
            source_s3_uri=source_uri,
            source_content_hash=source_content_hash,
            chunking_run_id=chunking_run_id,
            source_type="html",
        )
        return source_text, resolved_chunk_params_hash

    def _write_chunk_records(self, records: list[dict[str, Any]]) -> int:
        """Persist chunk records as artifacts and registry rows.

        Args:
            records: Chunk record dictionaries with source metadata, chunk content,
                run context, and destination key.

        Returns:
            Number of newly written chunk artifacts.

        Side Effects:
            - May write JSON chunk artifacts to object storage.
            - Writes one chunk artifact JSON object per chunk record.
        """
        self._initialize_manifest_state()
        for chunk_record in records:
            self.chunk_count_expected += 1
            destination_key = chunk_record["destination_key"]
            self.add_chunk_to_manifest(chunk_record)
            self._write_chunk_object(destination_key=destination_key, chunk_record=chunk_record)
            self.written += 1
        manifest = self._build_manifest()
        self._write_manifest(manifest)
        return self.written

    def _initialize_manifest_state(self) -> None:
        self.written = 0
        self.chunk_count_expected = 0
        self.chunk_entries = []

    def add_chunk_to_manifest(self, chunk_record: dict[str, Any]) -> None:
        self.chunk_entries.append(
            ChunkManifestEntry(
                chunk_id=chunk_record["chunk_id"],
                chunk_index=chunk_record["chunk_index"],
                chunk_hash=chunk_record["chunk_text_hash"],
                path=chunk_record["destination_key"],
            )
        )

    def _write_chunk_object(self, destination_key: str, chunk_record: dict[str, Any]) -> None:
        self.object_storage.write_object(
            self.storage_bucket,
            destination_key,
            json.dumps(chunk_record, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            content_type="application/json",
        )

    def _write_manifest(self, manifest: ChunkManifest) -> None:
        self.object_storage.write_object(
            self.storage_bucket,
            self._manifest_object_key(self.chunk_document_metadata.doc_id, self.chunk_document_metadata.chunking_run_id),
            json.dumps(manifest.to_dict(), sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            content_type="application/json",
        )

    def _build_manifest(self) -> ChunkManifest:
        source_uri = self.chunk_document_metadata.source_s3_uri
        lineage = ChunkManifestLineage(
            source_asset_id=source_uri,
            source_hash=sha256_hex(source_uri),
            content_type=self._manifest_content_type,
            document_hash=self.chunk_document_metadata.source_content_hash,
            parser_version=self._manifest_parser_version,
        )
        processing = ChunkManifestProcessing(
            run_id=self.chunk_document_metadata.chunking_run_id,
            stage=self.STAGE_NAME,
            timestamp=self.chunk_document_metadata.timestamp,
            chunker_version=self.CHUNKER_VERSION,
            run_status="complete" if self.written == self.chunk_count_expected else "partial",
            chunker=ChunkerConfig(
                strategy=self._chunking_params.strategy,
                chunk_size=self._chunking_params.chunk_size,
                chunk_overlap=self._chunking_params.chunk_overlap,
            ),
        )
        output = ChunkManifestOutput(
            chunk_count_expected=self.chunk_count_expected,
            chunk_count_written=self.written,
        )
        return ChunkManifest.build(
            doc_id=self.chunk_document_metadata.doc_id,
            lineage=lineage,
            processing=processing,
            output=output,
            chunks=self.chunk_entries,
        )

    def _chunk_object_key(self, doc_id: str, chunk_id: str) -> str:
        """Build the object storage key for a chunk artifact.

        Args:
            doc_id: Document identifier used as the folder component.
            chunk_id: Deterministic chunk identifier used as the filename stem.

        Returns:
            A storage key in the format:
            `{output_prefix}chunks/{doc_id}/run={run_id}/chunk={chunk_id}.json`.
        """
        run_id = self.chunk_document_metadata.chunking_run_id
        return f"{self.output_prefix.rstrip('/')}/{self.CHUNKS_DIR}/{doc_id}/run={run_id}/chunk={chunk_id}.json"

    def _manifest_object_key(self, doc_id: str, run_id: str) -> str:
        return f"{self.manifest_prefix.rstrip('/')}/{self.CHUNKS_MANIFEST_DIR}/{doc_id}/run={run_id}/{self.MANIFEST_FILE_NAME}"
