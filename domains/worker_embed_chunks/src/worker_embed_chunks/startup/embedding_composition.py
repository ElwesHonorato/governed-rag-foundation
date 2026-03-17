"""Embedding composition helpers for worker_embed_chunks startup."""

from __future__ import annotations

from dataclasses import dataclass

from ai_infra.retrieval.deterministic_hash_embedder import (
    DeterministicHashEmbedder,
)


@dataclass(frozen=True)
class EmbeddingComposition:
    """Shared embedding collaborators used by the embed worker."""

    embedder: DeterministicHashEmbedder


class EmbeddingCompositionFactory:
    """Build embedding collaborators from worker runtime configuration."""

    def build(self, dimension: int) -> EmbeddingComposition:
        return EmbeddingComposition(
            embedder=DeterministicHashEmbedder(dimensions=dimension)
        )
