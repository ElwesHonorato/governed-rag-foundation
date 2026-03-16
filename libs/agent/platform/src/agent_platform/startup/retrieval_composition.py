"""Shared retrieval composition helpers for the agent-platform runtime."""

from __future__ import annotations

from dataclasses import dataclass

from ai_infra.retrieval.deterministic_retrieval_embedder import (
    DeterministicRetrievalEmbedder,
)
from agent_platform.startup.contracts import RetrievalSettings


@dataclass(frozen=True)
class RetrievalComposition:
    """Shared retrieval collaborators used across bootstrap and runtime wiring."""

    embedder: DeterministicRetrievalEmbedder


class RetrievalCompositionFactory:
    """Build shared retrieval collaborators from runtime settings."""

    def build(self, settings: RetrievalSettings) -> RetrievalComposition:
        return RetrievalComposition(
            embedder=DeterministicRetrievalEmbedder(settings.embedding_dim)
        )
