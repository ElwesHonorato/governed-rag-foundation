"""Factory for retrieval embedder construction."""

from __future__ import annotations

from ai_infra.retrieval.deterministic_retrieval_embedder import (
    DeterministicRetrievalEmbedder,
)


class RetrievalEmbedderFactory:
    """Build retrieval embedders for local agent-platform startup."""

    def build(self, embedding_dim: int) -> DeterministicRetrievalEmbedder:
        return DeterministicRetrievalEmbedder(embedding_dim)
