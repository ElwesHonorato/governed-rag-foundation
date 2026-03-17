"""Factory for embedder construction."""

from __future__ import annotations

from ai_infra.retrieval.deterministic_hash_embedder import (
    DeterministicHashEmbedder,
)


class EmbedderFactory:
    """Build embedders for local agent-platform startup."""

    def build(self, embedding_dim: int) -> DeterministicHashEmbedder:
        return DeterministicHashEmbedder(embedding_dim)
