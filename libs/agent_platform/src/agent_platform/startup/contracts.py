"""Startup contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentPlatformConfig:
    """Resolved startup configuration."""

    repo_root: str
    workspace_root: str
    config_dir: str
    state_dir: str
    llm_url: str
    llm_model: str
    llm_timeout_seconds: int
