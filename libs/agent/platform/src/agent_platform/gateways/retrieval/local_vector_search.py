"""Local vector-search adapter."""

from __future__ import annotations

import json
from pathlib import Path

from agent_platform.gateways.retrieval.deterministic_embedding_fixture import (
    DeterministicEmbeddingFixture,
)


class LocalVectorSearch:
    """Queries the deterministic local vector fixture."""

    def __init__(self, index_path: str, embedder: DeterministicEmbeddingFixture) -> None:
        self._index_path = Path(index_path)
        self._embedder = embedder

    def search(self, query: str, top_k: int) -> list[dict[str, object]]:
        payload = json.loads(self._index_path.read_text())
        query_vector = self._embedder.embed(query)
        ranked = []
        for item in payload["documents"]:
            score = self._embedder.similarity(query_vector, item["vector"])
            ranked.append(
                {
                    "path": item["path"],
                    "score": round(score, 6),
                    "snippet": item["content"][:240],
                }
            )
        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked[:top_k]
