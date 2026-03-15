"""Startup config extraction."""

from __future__ import annotations

from pathlib import Path

from startup.contracts import AgentPlatformConfig


class AgentPlatformConfigExtractor:
    """Derives local configuration from the repository layout."""

    def extract(self) -> AgentPlatformConfig:
        repo_root = Path(__file__).resolve().parents[4]
        config_dir = repo_root / "domains" / "agent_platform" / "src" / "config"
        state_dir = repo_root / "domains" / "agent_platform" / "localdata"
        state_dir.mkdir(parents=True, exist_ok=True)
        return AgentPlatformConfig(
            repo_root=str(repo_root),
            workspace_root=str(repo_root),
            config_dir=str(config_dir),
            state_dir=str(state_dir),
        )
