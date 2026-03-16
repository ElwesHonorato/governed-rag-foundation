"""Shared retrieval composition helpers for the agent-platform runtime."""

from __future__ import annotations

from dataclasses import dataclass

from ai_infra.retrieval.deterministic_retrieval_embedder import (
    DeterministicRetrievalEmbedder,
)


@dataclass(frozen=True)
class RetrievalComposition:
    """Shared retrieval collaborators used across bootstrap and runtime wiring."""

    embedder: DeterministicRetrievalEmbedder
