import json
import tempfile
from pathlib import Path
from typing import Any

from pipeline_common.gateways.processing_engine import SparkWriteGateway


class IndexWeaviateProcessor:
    """Build indexing instructions and status payloads."""

    def __init__(
        self,
        *,
        output_prefix: str,
        spark_session: Any | None,
    ) -> None:
        self.output_prefix = output_prefix
        self.spark_session = spark_session

    @staticmethod
    def read_embeddings_payload(raw_payload: bytes) -> dict[str, Any]:
        return dict(json.loads(raw_payload.decode("utf-8", errors="ignore")))

    def build_upsert_items(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        return self._build_upsert_items_local(payload)

    def build_input_records(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Normalize payload into dataframe-ready records."""
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
                    "doc_id": metadata.get("doc_id"),
                    "chunk_text": metadata.get("chunk_text"),
                    "source_key": metadata.get("source_key"),
                    "security_clearance": metadata.get("security_clearance"),
                    "chunking_run_id": metadata.get("chunking_run_id"),
                    "embedder_name": metadata.get("embedder_name"),
                    "embedder_version": metadata.get("embedder_version"),
                    "embedding_params_hash": metadata.get("embedding_params_hash"),
                    "embedding_run_id": metadata.get("embedding_run_id"),
                }
            )
        return records

    def build_upsert_items_from_dataframe(
        self,
        input_df: Any,
        *,
        write_gateway: SparkWriteGateway,
    ) -> list[dict[str, Any]]:
        """Transform dataframe and materialize upsert items via write gateway."""
        transformed_df = self._build_upsert_dataframe(input_df)
        records = self._materialize_records_from_dataframe(
            transformed_df,
            write_gateway=write_gateway,
        )
        items: list[dict[str, Any]] = []
        for row in records:
            chunk_id = str(row["chunk_id"])
            items.append(
                {
                    "chunk_id": chunk_id,
                    "vector": row.get("vector", []),
                    "properties": {
                        "chunk_id": chunk_id,
                        "doc_id": row.get("doc_id"),
                        "chunk_text": row.get("chunk_text"),
                        "source_key": row.get("source_key"),
                        "security_clearance": row.get("security_clearance"),
                        "chunking_run_id": row.get("chunking_run_id"),
                        "embedder_name": row.get("embedder_name"),
                        "embedder_version": row.get("embedder_version"),
                        "embedding_params_hash": row.get("embedding_params_hash"),
                        "embedding_run_id": row.get("embedding_run_id"),
                    },
                }
            )
        return items

    @staticmethod
    def _build_upsert_dataframe(input_df: Any) -> Any:
        return input_df.select(
            "chunk_id",
            "vector",
            "doc_id",
            "chunk_text",
            "source_key",
            "security_clearance",
            "chunking_run_id",
            "embedder_name",
            "embedder_version",
            "embedding_params_hash",
            "embedding_run_id",
        )

    def _materialize_records_from_dataframe(
        self,
        dataframe: Any,
        *,
        write_gateway: SparkWriteGateway,
    ) -> list[dict[str, Any]]:
        with tempfile.TemporaryDirectory(prefix="worker_index_weaviate_") as temp_dir:
            write_gateway.write(
                dataframe,
                path=temp_dir,
                format_name="json",
                mode="overwrite",
            )
            json_parts = sorted(Path(temp_dir).glob("part-*"))
            return self._read_json_parts_as_records(json_parts)

    @staticmethod
    def _read_json_parts_as_records(json_parts: list[Path]) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for part in json_parts:
            with part.open("r", encoding="utf-8") as handle:
                for line in handle:
                    records.append(dict(json.loads(line)))
        return records

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
                        "chunking_run_id": metadata.get("chunking_run_id"),
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
            return f"{self.output_prefix}{doc_id}/{chunk_id}.indexed.json"
        return f"{self.output_prefix}{doc_id}.indexed.json"

    @staticmethod
    def build_index_status_payload(doc_id: str, chunk_id: str) -> dict[str, Any]:
        status_payload: dict[str, Any] = {"doc_id": doc_id, "status": "indexed"}
        if chunk_id:
            status_payload["chunk_id"] = chunk_id
        return status_payload
