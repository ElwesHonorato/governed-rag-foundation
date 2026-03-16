"""Startup contracts."""

from __future__ import annotations

from dataclasses import dataclass

from agent_settings.settings import LLMSettings, RetrievalSettings


@dataclass(frozen=True)
class RuntimePaths:
    """Resolved runtime paths used by the local agent runtime."""

    workspace_root: str
    state_dir: str

@dataclass(frozen=True)
class AgentPlatformConfig:
    """Resolved startup configuration grouped by component."""

    paths: RuntimePaths
    llm: LLMSettings
    retrieval: RetrievalSettings
