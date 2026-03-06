"""Golden-path provenance registry backed by object storage latest-state JSON."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from pipeline_common.stages_contracts.stage_30_chunking import (
    ChunkRegistryRow,
)
from pipeline_common.stages_contracts.stage_40_embedding import (
    EmbeddingProvenanceEnvelope,
    EmbeddingRegistryRow,
    EmbeddingRegistryStatus,
)
from pipeline_common.provenance.identifiers import sha256_hex

if TYPE_CHECKING:
    from pipeline_common.gateways.object_storage import ObjectStorageGateway


def _utc_now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")


class ProvenanceRegistryGateway:
    """Persist and query chunk/embedding provenance for the golden path only."""

    def __init__(
        self,
        *,
        object_storage: "ObjectStorageGateway",
        bucket: str,
        base_prefix: str = "07_metadata/provenance/",
    ) -> None:
        self._object_storage = object_storage
        self._bucket = bucket
        self._base_prefix = base_prefix

    def upsert_chunk(self, row: ChunkRegistryRow) -> ChunkRegistryRow:
        """Write latest chunk registry state by chunk_id."""
        latest_key = self._chunk_latest_key(row.chunk_id)
        payload = row.dump()
        self._object_storage.write_object(self._bucket, latest_key, _json_bytes(payload), content_type="application/json")
        return row

    def upsert_embedding_succeeded(self, row: EmbeddingRegistryRow) -> EmbeddingRegistryRow:
        """Write latest embedding registry state by embedding_id."""
        payload = row.dump()
        payload["status"] = EmbeddingRegistryStatus.SUCCEEDED.value
        payload["upserted_at"] = _utc_now_iso()
        latest_key = self._embedding_latest_key(str(row.embedding_id))
        self._object_storage.write_object(self._bucket, latest_key, _json_bytes(payload), content_type="application/json")
        self._object_storage.write_object(
            self._bucket,
            self._embedding_pair_latest_key(str(row.chunk_id), str(row.index_target)),
            _json_bytes({"embedding_id": str(row.embedding_id), "upserted_at": str(payload["upserted_at"])}),
            content_type="application/json",
        )
        envelope = EmbeddingProvenanceEnvelope(
            embedding_id=str(payload["embedding_id"]),
            chunk_id=str(payload["chunk_id"]),
            index_target=str(payload["index_target"]),
            embedder_name=str(payload["embedder_name"]),
            embedder_version=str(payload["embedder_version"]),
            embedding_params_hash=str(payload["embedding_params_hash"]),
            embedding_dim=int(payload["embedding_dim"]),
            embedding_vector_hash=str(payload["embedding_vector_hash"]) if payload.get("embedding_vector_hash") else None,
            embedding_run_id=str(payload["embedding_run_id"]),
            chunking_run_id=str(payload["chunking_run_id"]),
            vector_record_id=str(payload["vector_record_id"]) if payload.get("vector_record_id") else None,
        )
        return EmbeddingRegistryRow.from_envelope(
            envelope=envelope,
            attempt=int(payload.get("attempt", 1)),
            status=EmbeddingRegistryStatus.SUCCEEDED,
            error_message=None,
            started_at=str(payload["started_at"]),
            finished_at=str(payload["finished_at"]) if payload.get("finished_at") else None,
            upserted_at=str(payload["upserted_at"]),
        )

    def get_chunk_provenance(self, chunk_id: str) -> dict[str, Any] | None:
        payload = self._read_json_if_exists(self._chunk_latest_key(chunk_id))
        return dict(payload) if isinstance(payload, dict) else None

    def get_embedding_provenance(self, chunk_id: str, index_target: str) -> dict[str, Any] | None:
        mapping = self._read_json_if_exists(self._embedding_pair_latest_key(chunk_id, index_target))
        if not isinstance(mapping, dict):
            return None
        embedding_id = str(mapping.get("embedding_id", ""))
        if not embedding_id:
            return None
        payload = self._read_json_if_exists(self._embedding_latest_key(embedding_id))
        return dict(payload) if isinstance(payload, dict) else None

    def trace_from_vector_result(self, chunk_id: str, index_target: str) -> dict[str, Any]:
        return {
            "chunk_id": chunk_id,
            "index_target": index_target,
            "chunk": self.get_chunk_provenance(chunk_id),
            "embedding": self.get_embedding_provenance(chunk_id, index_target),
        }

    def _read_json_if_exists(self, key: str) -> dict[str, Any] | None:
        if not self._object_storage.object_exists(self._bucket, key):
            return None
        raw = self._object_storage.read_object(self._bucket, key)
        return dict(json.loads(raw.decode("utf-8")))

    def _chunk_latest_key(self, chunk_id: str) -> str:
        return f"{self._base_prefix}chunking/latest/{chunk_id}.json"

    def _embedding_latest_key(self, embedding_id: str) -> str:
        return f"{self._base_prefix}embedding/latest/{embedding_id}.json"

    def _embedding_pair_latest_key(self, chunk_id: str, index_target: str) -> str:
        ref = sha256_hex(f"{chunk_id}|{index_target}")
        return f"{self._base_prefix}embedding/latest_by_pair/{ref}.json"
