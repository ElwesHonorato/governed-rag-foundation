import hashlib
import json
from dataclasses import dataclass
from typing import Any

from pipeline_common.gateways.object_storage import ObjectStorageGateway


@dataclass(frozen=True)
class EmbeddingWriteResult:
    destination_key: str
    doc_id: str
    chunk_id: str
    wrote: bool


class EmbedChunksProcessor:
    """Build embedding payloads from chunk payloads and write outputs."""

    def __init__(
        self,
        *,
        dimension: int,
        spark_session: Any | None,
        object_storage: ObjectStorageGateway,
        storage_bucket: str,
        output_prefix: str,
    ) -> None:
        self.dimension = dimension
        self.spark_session = spark_session
        self.object_storage = object_storage
        self.storage_bucket = storage_bucket
        self.output_prefix = output_prefix

    @staticmethod
    def _deterministic_embedding_for(text: str, dimension: int) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        for index in range(dimension):
            byte = digest[index % len(digest)]
            values.append((byte / 255.0) * 2.0 - 1.0)
        return values

    @staticmethod
    def read_chunk_payload(raw_payload: bytes) -> dict[str, Any]:
        return dict(json.loads(raw_payload.decode("utf-8", errors="ignore")))

    def write_embedding_artifact(self, payload: dict[str, Any]) -> EmbeddingWriteResult:
        embedding_payload = self._build_embedding_payload_local(payload)
        doc_id = str(embedding_payload["doc_id"])
        chunk_id = str(embedding_payload["chunk_id"])
        destination_key = self._embedding_object_key(doc_id, chunk_id)
        if self.object_storage.object_exists(self.storage_bucket, destination_key):
            return EmbeddingWriteResult(destination_key=destination_key, doc_id=doc_id, chunk_id=chunk_id, wrote=False)
        self.object_storage.write_object(
            self.storage_bucket,
            destination_key,
            json.dumps(embedding_payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            content_type="application/json",
        )
        return EmbeddingWriteResult(destination_key=destination_key, doc_id=doc_id, chunk_id=chunk_id, wrote=True)

    def build_input_dataframe(self, payload: dict[str, Any]) -> Any:
        """Create Spark DataFrame input for embedding transforms."""
        if self.spark_session is None:
            raise RuntimeError("Spark session is required for DataFrame processing")
        text = str(payload["chunk_text"])
        input_row = {
            "doc_id": str(payload.get("doc_id")),
            "chunk_id": str(payload["chunk_id"]),
            "chunk_text": text,
            "source_type": payload.get("source_type"),
            "timestamp": payload.get("timestamp"),
            "security_clearance": payload.get("security_clearance"),
            "source_key": payload.get("source_key"),
            "chunk_index": payload.get("chunk_index"),
            "dimension": int(self.dimension),
        }
        return self.spark_session.createDataFrame([input_row])

    def write_embedding_artifact_from_dataframe(self, input_df: Any) -> EmbeddingWriteResult:
        """Transform Spark DataFrame row into embedding artifact and write output."""
        embedding_payload = self._build_embedding_payload_spark(input_df)
        doc_id = str(embedding_payload["doc_id"])
        chunk_id = str(embedding_payload["chunk_id"])
        destination_key = self._embedding_object_key(doc_id, chunk_id)
        if self.object_storage.object_exists(self.storage_bucket, destination_key):
            return EmbeddingWriteResult(destination_key=destination_key, doc_id=doc_id, chunk_id=chunk_id, wrote=False)
        self.object_storage.write_object(
            self.storage_bucket,
            destination_key,
            json.dumps(embedding_payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            content_type="application/json",
        )
        return EmbeddingWriteResult(destination_key=destination_key, doc_id=doc_id, chunk_id=chunk_id, wrote=True)

    def _build_embedding_payload_local(self, payload: dict[str, Any]) -> dict[str, Any]:
        text = str(payload["chunk_text"])
        doc_id = str(payload.get("doc_id"))
        chunk_id = str(payload["chunk_id"])
        return {
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "vector": self._deterministic_embedding_for(text, self.dimension),
            "metadata": self._metadata_from_payload(payload, doc_id, text),
        }

    def _build_embedding_payload_spark(self, input_df: Any) -> dict[str, Any]:
        from pyspark.sql import functions as F  # type: ignore
        from pyspark.sql import types as T  # type: ignore

        vector_udf = F.udf(
            lambda value, dim: self._deterministic_embedding_for(str(value), int(dim)),
            T.ArrayType(T.DoubleType()),
        )
        row = input_df.withColumn("vector", vector_udf(F.col("chunk_text"), F.col("dimension"))).collect()[0]
        doc_id = str(row["doc_id"])
        chunk_id = str(row["chunk_id"])
        text = str(row["chunk_text"])
        row_payload = {
            "source_type": row["source_type"],
            "timestamp": row["timestamp"],
            "security_clearance": row["security_clearance"],
            "source_key": row["source_key"],
            "chunk_index": row["chunk_index"],
            "chunk_text": text,
        }
        return {
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "vector": list(row["vector"]),
            "metadata": self._metadata_from_payload(row_payload, doc_id, text),
        }

    @staticmethod
    def _metadata_from_payload(payload: dict[str, Any], doc_id: str, text: str) -> dict[str, Any]:
        return {
            "source_type": payload.get("source_type"),
            "timestamp": payload.get("timestamp"),
            "security_clearance": payload.get("security_clearance"),
            "doc_id": doc_id,
            "source_key": payload.get("source_key"),
            "chunk_index": payload.get("chunk_index"),
            "chunk_text": text,
        }

    def _embedding_object_key(self, doc_id: str, chunk_id: str) -> str:
        return f"{self.output_prefix}{doc_id}/{chunk_id}.embedding.json"
