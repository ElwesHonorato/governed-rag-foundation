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
