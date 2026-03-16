"""Startup contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent_settings.settings import LLMSettings, RetrievalSettings


@dataclass(frozen=True)
class RuntimePaths:
    """Resolved runtime paths used by the local agent runtime."""

    workspace_root: Path
    state_dir: Path
    vector_fixture_dir: Path
    vector_index_path: Path
    sessions_dir: Path
    runs_dir: Path
    checkpoints_dir: Path

@dataclass(frozen=True)
class AgentPlatformConfig:
    """Resolved startup configuration grouped by component."""

    paths: RuntimePaths
    llm: LLMSettings
    retrieval: RetrievalSettings
