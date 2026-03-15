"""Startup config extraction."""

from __future__ import annotations

import os
from pathlib import Path

from agent_platform.startup.contracts import AgentPlatformConfig


class AgentPlatformConfigExtractor:
    """Derives local configuration from the repository layout."""

    def extract(self) -> AgentPlatformConfig:
        package_root = Path(__file__).resolve().parents[1]
        workspace_root = Path(os.environ.get("AGENT_PLATFORM_WORKSPACE_ROOT", Path.cwd())).resolve()
        config_dir = package_root / "config"
        default_state_dir = workspace_root / ".agent_platform" / "localdata"
        state_dir = Path(os.environ.get("AGENT_PLATFORM_STATE_DIR", default_state_dir)).resolve()
        state_dir.mkdir(parents=True, exist_ok=True)
        return AgentPlatformConfig(
            repo_root=str(workspace_root),
            workspace_root=str(workspace_root),
            config_dir=str(config_dir),
            state_dir=str(state_dir),
        )
