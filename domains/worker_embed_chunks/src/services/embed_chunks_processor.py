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

    def _deterministic_embedding(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        for index in range(self.dimension):
            byte = digest[index % len(digest)]
            values.append((byte / 255.0) * 2.0 - 1.0)
        return values

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
            "vector": self._deterministic_embedding(text),
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
