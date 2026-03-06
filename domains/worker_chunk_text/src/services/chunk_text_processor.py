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
from contracts.contracts import ChunkingParamsContract

class ChunkTextProcessor:
    """Transform processed document rows into persisted chunk artifacts.

    The processor handles the full chunking pipeline for a single dataframe batch:
    normalize/expand rows into chunk rows, materialize rows into Python records,
    write chunk artifact objects.
    """
    CHUNKER_VERSION: ClassVar[str] = "1.0.0"

    def __init__(
        self,
        *,
        object_storage: ObjectStorageGateway,
        storage_bucket: str,
        output_prefix: str,
        chunking_params: ChunkingParamsContract,
    ) -> None:
        """Initialize processor dependencies and storage routing configuration.

        Args:
            object_storage: Gateway used to read/write chunk artifacts in object storage.
            storage_bucket: Bucket name where chunk artifacts are persisted.
            output_prefix: Key prefix under the bucket for chunk artifacts.

        Returns:
            None.
        """
        self.object_storage = object_storage
        self.storage_bucket = storage_bucket
        self.output_prefix = output_prefix
        self._chunking_params = chunking_params
        self.chunk_write_batch = {}
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunking_params.chunk_size,
            chunk_overlap=chunking_params.chunk_overlap,
            add_start_index=chunking_params.add_start_index,
        )

    def process(
        self,
        processed_payload: ProcessedDocumentPayload,
        *,
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
        written = 0
        self._initialize_chunk_write_batch()
        for chunk_record in records:
            destination_key = chunk_record["destination_key"]
            self._add_chunk_to_write_batch(
                chunk_id=chunk_record["chunk_id"],
                destination_key=destination_key,
            )
            self._write_chunk_object(destination_key=destination_key, chunk_record=chunk_record)
            written += 1
        self._set_chunk_write_batch_summary(records_count=len(records), written=written)
        return written

    def _build_chunk_records_from_payload(
        self,
        payload: ProcessedDocumentPayload,
        *,
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
        source_text = str(payload.parsed["text"])
        source_content_hash = sha256_hex(source_text)
        resolved_chunk_params_hash = chunk_params_hash(self._chunking_params.to_dict())
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

    def _initialize_chunk_write_batch(self) -> None:
        self.chunk_write_batch = {
            "source_metadata": self.chunk_document_metadata.to_dict(),
            "run_summary": {},
            "chunks": {},
        }

    def _add_chunk_to_write_batch(self, *, chunk_id: str, destination_key: str) -> None:
        self.chunk_write_batch["chunks"][chunk_id] = {
            "destination_key": destination_key,
        }

    def _write_chunk_object(self, *, destination_key: str, chunk_record: dict[str, Any]) -> None:
        self.object_storage.write_object(
            self.storage_bucket,
            destination_key,
            json.dumps(chunk_record, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            content_type="application/json",
        )

    def _set_chunk_write_batch_summary(self, *, records_count: int, written: int) -> None:
        self.chunk_write_batch["run_summary"] = {
            "source_metadata": self.chunk_document_metadata.to_dict(),
            "processor_class": self.__class__.__name__,
            "chunker_version": self.CHUNKER_VERSION,
            "chunking_params": self._chunking_params.to_dict(),
            "records_total": records_count,
            "records_written": written,
            "records_existing": records_count - written,
        }

    def _chunk_object_key(self, doc_id: str, chunk_id: str) -> str:
        """Build the object storage key for a chunk artifact.

        Args:
            doc_id: Document identifier used as the folder component.
            chunk_id: Deterministic chunk identifier used as the filename stem.

        Returns:
            A storage key in the format:
            `{output_prefix}{doc_id}/{chunk_id}.chunk.json`.
        """
        return f"{self.output_prefix}{doc_id}/{chunk_id}.chunk.json"
