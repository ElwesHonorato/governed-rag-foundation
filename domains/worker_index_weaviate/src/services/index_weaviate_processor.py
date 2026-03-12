import json
from typing import Any


class IndexWeaviateProcessor:
    """Build indexing instructions and status payloads."""

    def __init__(
        self,
        *,
        storage_bucket: str,
        output_prefix: str,
    ) -> None:
        self._storage_bucket = storage_bucket
        self._output_prefix = output_prefix

    @staticmethod
    def read_embeddings_payload(raw_payload: bytes) -> dict[str, Any]:
        return dict(json.loads(raw_payload.decode("utf-8", errors="ignore")))

    def build_upsert_items(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        return self._build_upsert_items_local(payload)

    @staticmethod
    def _build_upsert_items_local(payload: dict[str, Any]) -> list[dict[str, Any]]:
        if isinstance(payload.get("embeddings"), list):
            items = payload.get("embeddings", [])
        else:
            items = [payload]
        records: list[dict[str, Any]] = []
        for item in items:
            metadata = dict(item.get("metadata", {}))
            chunk_id = str(item["chunk_id"])
            records.append(
                {
                    "chunk_id": chunk_id,
                    "vector": item.get("vector", []),
                    "properties": {
                        "chunk_id": chunk_id,
                        "doc_id": metadata.get("doc_id"),
                        "chunk_text": metadata.get("chunk_text"),
                        "source_key": metadata.get("source_key"),
                        "security_clearance": metadata.get("security_clearance"),
                        "run_id": metadata.get("run_id"),
                        "embedder_name": metadata.get("embedder_name"),
                        "embedder_version": metadata.get("embedder_version"),
                        "embedding_params_hash": metadata.get("embedding_params_hash"),
                        "embedding_run_id": metadata.get("embedding_run_id"),
                    },
                }
            )
        return records

    def build_indexed_key(self, doc_id: str, chunk_id: str) -> str:
        if chunk_id:
            return f"{self._output_prefix}{doc_id}/{chunk_id}.indexed.json"
        return f"{self._output_prefix}{doc_id}.indexed.json"

    def status_exists(self, object_storage: Any, destination_key: str) -> bool:
        """Return whether the indexed status object already exists."""
        return object_storage.object_exists(self._storage_bucket, destination_key)

    def destination_name(self, destination_key: str) -> str:
        """Build the lineage output dataset name for a written status artifact."""
        return f"{self._storage_bucket}/{destination_key}"

    @staticmethod
    def build_index_status_payload(doc_id: str, chunk_id: str) -> dict[str, Any]:
        status_payload: dict[str, Any] = {"doc_id": doc_id, "status": "indexed"}
        if chunk_id:
            status_payload["chunk_id"] = chunk_id
        return status_payload
