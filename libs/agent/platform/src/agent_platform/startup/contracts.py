"""Startup contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LLMParams:
    """Runtime LLM parameters owned by the composition root."""

    llm_timeout_seconds: int


@dataclass(frozen=True)
class RetrievalParams:
    """Runtime retrieval parameters owned by the composition root."""

    retrieval_limit: int


@dataclass(frozen=True)
class EmbedderParams:
    """Runtime embedder parameters owned by the composition root."""

    embedding_dim: int


@dataclass(frozen=True)
class RuntimePaths:
    """Resolved runtime paths used by the local agent runtime."""

    workspace_root: Path
    vector_fixture_dir: Path
    vector_index_path: Path
    vector_index_ignore_path: Path
    sessions_dir: Path
    runs_dir: Path
    checkpoints_dir: Path

@dataclass(frozen=True)
class AgentPlatformConfig:
    """Resolved startup configuration grouped by component."""

    paths: RuntimePaths
    llm: LLMParams
    retrieval: RetrievalParams
    embedder: EmbedderParams
