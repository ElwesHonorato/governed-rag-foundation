import json
from typing import Any

from chunking.domain.text_chunker import chunk_text
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.provenance import (
    ChunkProvenanceEnvelope,
    ChunkRegistryRow,
    ChunkRegistryStatus,
    ProvenanceRegistryGateway,
    build_chunk_id,
    sha256_hex,
)
from pipeline_common.provenance import chunk_params_hash
from pipeline_common.helpers.contracts import utc_now_iso
from pipeline_common.stages_contracts import ProcessedDocumentMetadata, ProcessedDocumentPayload

CHUNKER_NAME = "text_chunker"
CHUNKER_VERSION = "1.0.0"
CHUNKER_PARAMS = {"strategy": "default"}


class ChunkTextProcessor:
    """Transform processed document rows into persisted chunk artifacts.

    The processor handles the full chunking pipeline for a single dataframe batch:
    normalize/expand rows into chunk rows, materialize rows into Python records,
    write chunk artifact objects, and upsert chunk provenance registry entries.
    """

    def __init__(
        self,
        *,
        object_storage: ObjectStorageGateway,
        provenance_registry: ProvenanceRegistryGateway,
        storage_bucket: str,
        output_prefix: str,
    ) -> None:
        """Initialize processor dependencies and storage routing configuration.

        Args:
            object_storage: Gateway used to read/write chunk artifacts in object storage.
            provenance_registry: Gateway used to upsert chunk provenance registry rows.
            storage_bucket: Bucket name where chunk artifacts are persisted.
            output_prefix: Key prefix under the bucket for chunk artifacts.

        Returns:
            None.
        """
        self.object_storage = object_storage
        self.provenance_registry = provenance_registry
        self.storage_bucket = storage_bucket
        self.output_prefix = output_prefix

    def write_chunk_artifacts_from_payload(
        self,
        processed_payload: dict[str, Any],
        *,
        source_uri: str,
        chunking_run_id: str,
    ) -> tuple[int, list[str]]:
        """Run chunk expansion and persistence for a processed-document payload.

        Args:
            processed_payload: Parsed processed-document payload object.
            source_uri: Canonical source dataset URI.
            chunking_run_id: Run identifier for provenance stamping.

        Returns:
            A tuple `(written_count, destination_keys)` where:
            - `written_count` is the number of new chunk artifact objects created.
            - `destination_keys` contains all computed chunk object keys for the batch,
              including keys that may already have existed.

        Side Effects:
            Writes chunk artifact objects to object storage (if missing) and upserts
            chunk provenance rows in the registry.
        """
        records = self._build_chunk_records_from_payload(
            processed_payload,
            source_uri=source_uri,
            chunking_run_id=chunking_run_id,
        )
        return self._write_chunk_records(records)

    def _write_chunk_records(self, records: list[dict[str, Any]]) -> tuple[int, list[str]]:
        """Persist chunk records as artifacts and registry rows.

        Args:
            records: Chunk record dictionaries with source metadata, chunk content,
                run context, precomputed envelope, and destination key.

        Returns:
            A tuple `(written_count, destination_keys)` where:
            - `written_count` is incremented only when a chunk object did not already
              exist and was newly written.
            - `destination_keys` contains one storage key per input record.

        Side Effects:
            - May write JSON chunk artifacts to object storage.
            - Always upserts a provenance registry row per chunk record.
        """
        written = 0
        destination_keys: list[str] = []
        for chunk_record in records:
            envelope = chunk_record["envelope"]
            destination_key = str(chunk_record["destination_key"])
            destination_keys.append(destination_key)
            artifact_payload = {
                key: value for key, value in chunk_record.items() if key not in {"envelope", "destination_key"}
            }
            artifact_payload["chunk_id"] = envelope.chunk_id
            artifact_payload["provenance"] = envelope.to_dict()
            if not self.object_storage.object_exists(self.storage_bucket, destination_key):
                self.object_storage.write_object(
                    self.storage_bucket,
                    destination_key,
                    json.dumps(artifact_payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode(
                        "utf-8"
                    ),
                    content_type="application/json",
                )
                written += 1
            now_iso = utc_now_iso()
            self.provenance_registry.upsert_chunk(
                ChunkRegistryRow.from_envelope(
                    envelope=envelope,
                    created_at=now_iso,
                    observed_at=now_iso,
                    status=ChunkRegistryStatus.ACTIVE,
                )
            )
        return written, destination_keys

    def _chunk_segments(self, source_text: str) -> list[tuple[int, str, int, int]]:
        """Split source text into chunk segments with offsets."""
        chunks = chunk_text(source_text)
        cursor = 0
        segments: list[tuple[int, str, int, int]] = []
        for index, chunk_value in enumerate(chunks):
            resolved = source_text.find(chunk_value, cursor)
            start = resolved if resolved >= 0 else cursor
            end = start + len(chunk_value)
            segments.append((index, chunk_value, start, end))
            cursor = end
        return segments

    def _build_chunk_records_from_payload(
        self,
        payload: dict[str, Any],
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
        parsed = payload[ProcessedDocumentPayload.FIELD_PARSED]
        source_text = str(parsed["text"])
        metadata = ProcessedDocumentMetadata(
            schema_version=str(payload[ProcessedDocumentMetadata.FIELD_SCHEMA_VERSION]),
            doc_id=str(payload[ProcessedDocumentMetadata.FIELD_DOC_ID]),
            source_key=str(payload[ProcessedDocumentMetadata.FIELD_SOURCE_KEY]),
            timestamp=str(payload[ProcessedDocumentMetadata.FIELD_TIMESTAMP]),
            security_clearance=str(payload[ProcessedDocumentMetadata.FIELD_SECURITY_CLEARANCE]),
        )
        doc_id = metadata.doc_id
        source_content_hash = sha256_hex(source_text)
        resolved_chunk_params_hash = chunk_params_hash(CHUNKER_PARAMS)

        records: list[dict[str, Any]] = []
        for chunk_index, chunk_text_value, offsets_start, offsets_end in self._chunk_segments(source_text):
            resolved_chunk_text_hash = sha256_hex(chunk_text_value)
            resolved_chunk_id = build_chunk_id(
                source_dataset_urn=source_uri,
                source_content_hash_value=source_content_hash,
                chunker_name=CHUNKER_NAME,
                chunker_version=CHUNKER_VERSION,
                chunk_params_hash_value=resolved_chunk_params_hash,
                offsets_start=offsets_start,
                offsets_end=offsets_end,
            )
            destination_key = self._chunk_object_key(doc_id, resolved_chunk_id)
            envelope = ChunkProvenanceEnvelope(
                chunk_id=resolved_chunk_id,
                source_dataset_urn=source_uri,
                source_s3_uri=source_uri,
                source_content_hash=source_content_hash,
                chunk_s3_uri=f"s3://{self.storage_bucket}/{destination_key}",
                offsets_start=int(offsets_start),
                offsets_end=int(offsets_end),
                chunk_text_hash=resolved_chunk_text_hash,
                chunker_name=CHUNKER_NAME,
                chunker_version=CHUNKER_VERSION,
                chunking_run_id=chunking_run_id,
                chunk_params_hash=resolved_chunk_params_hash,
                breadcrumb=f"chunk[{chunk_index}]",
            )
            records.append(
                {
                    "doc_id": doc_id,
                    "chunk_id": envelope.chunk_id,
                    "chunk_index": chunk_index,
                    "chunk_text": chunk_text_value,
                    "source_type": "html",
                    "timestamp": metadata.timestamp,
                    "security_clearance": metadata.security_clearance,
                    "source_dataset_urn": source_uri,
                    "source_s3_uri": source_uri,
                    "source_content_hash": source_content_hash,
                    "offsets_start": offsets_start,
                    "offsets_end": offsets_end,
                    "breadcrumb": envelope.breadcrumb,
                    "chunking_run_id": chunking_run_id,
                    "destination_key": destination_key,
                    "envelope": envelope,
                }
            )
        return records

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
