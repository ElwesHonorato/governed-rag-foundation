"""Startup contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from agent_settings.settings import LLMSettings, RetrievalSettings


class LLMRetrievalConfig(Protocol):
    """Startup configuration that exposes only LLM and retrieval settings."""

    llm: LLMSettings
    retrieval: RetrievalSettings


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
    llm: LLMSettings
    retrieval: RetrievalSettings
