import hashlib
import json
from typing import Any


class EmbedChunksProcessor:
    """Build embedding payloads from chunk payloads."""

    def __init__(
        self,
        *,
        dimension: int,
        spark_session: Any | None,
    ) -> None:
        self.dimension = dimension
        self.spark_session = spark_session

    @staticmethod
    def _deterministic_embedding_for(text: str, dimension: int) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        for index in range(dimension):
            byte = digest[index % len(digest)]
            values.append((byte / 255.0) * 2.0 - 1.0)
        return values

    def _build_vector(self, text: str) -> list[float]:
        """Build embedding vector using Spark when available, else local Python."""
        if self.spark_session is None:
            return self._deterministic_embedding_for(text, self.dimension)
        return list(
            self.spark_session.sparkContext
            .parallelize([text], 1)
            .map(lambda item: self._deterministic_embedding_for(item, self.dimension))
            .collect()[0]
        )

    @staticmethod
    def read_chunk_payload(raw_payload: bytes) -> dict[str, Any]:
        return dict(json.loads(raw_payload.decode("utf-8", errors="ignore")))

    def build_embedding_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        text = str(payload["chunk_text"])
        doc_id = str(payload.get("doc_id"))
        chunk_id = str(payload["chunk_id"])
        return {
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "vector": self._build_vector(text),
            "metadata": {
                "source_type": payload.get("source_type"),
                "timestamp": payload.get("timestamp"),
                "security_clearance": payload.get("security_clearance"),
                "doc_id": doc_id,
                "source_key": payload.get("source_key"),
                "chunk_index": payload.get("chunk_index"),
                "chunk_text": text,
            },
        }
