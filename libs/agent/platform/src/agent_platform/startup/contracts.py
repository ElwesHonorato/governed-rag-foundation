"""Startup contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent_settings.settings import LLMSettings, RetrievalSettings


@dataclass(frozen=True)
class LLMConfig:
    """Runtime LLM configuration owned by the composition root."""

    settings: LLMSettings
    llm_timeout_seconds: int


@dataclass(frozen=True)
class RetrievalConfig:
    """Runtime retrieval configuration owned by the composition root."""

    settings: RetrievalSettings
    embedding_dim: int
    retrieval_limit: int


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
    llm: LLMConfig
    retrieval: RetrievalConfig
