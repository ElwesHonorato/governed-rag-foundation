"""Factory for embedder construction."""

from __future__ import annotations

from ai_infra.retrieval.deterministic_hash_embedder import (
    DeterministicHashEmbedder,
)


class EmbedderFactory:
    """Build embedders for local agent-platform startup."""

    def __init__(self, *, embedder: DeterministicHashEmbedder) -> None:
        self._embedder = embedder

    def build(self) -> DeterministicHashEmbedder:
        return self._embedder
