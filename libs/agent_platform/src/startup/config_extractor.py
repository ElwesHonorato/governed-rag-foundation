"""Startup config extraction."""

from __future__ import annotations

import os
from pathlib import Path

from startup.contracts import AgentPlatformConfig


class AgentPlatformConfigExtractor:
    """Derives local configuration from the repository layout."""

    def extract(self) -> AgentPlatformConfig:
        package_root = Path(__file__).resolve().parents[1]
        workspace_root = Path(os.environ.get("AGENT_PLATFORM_WORKSPACE_ROOT", Path.cwd())).resolve()
        config_dir = package_root / "config"
        default_state_dir = workspace_root / ".agent_platform" / "localdata"
        state_dir = Path(os.environ.get("AGENT_PLATFORM_STATE_DIR", default_state_dir)).resolve()
        llm_url = self._required_env("LLM_URL")
        llm_model = self._required_env("LLM_MODEL")
        llm_timeout_seconds = self._required_int_env("LLM_TIMEOUT_SECONDS")
        state_dir.mkdir(parents=True, exist_ok=True)
        return AgentPlatformConfig(
            repo_root=str(workspace_root),
            workspace_root=str(workspace_root),
            config_dir=str(config_dir),
            state_dir=str(state_dir),
            llm_url=llm_url,
            llm_model=llm_model,
            llm_timeout_seconds=llm_timeout_seconds,
        )

    @staticmethod
    def _required_env(name: str) -> str:
        value = os.environ.get(name)
        if not value:
            raise ValueError(f"{name} is not configured")
        return value.strip()

    def _required_int_env(self, name: str) -> int:
        raw_value = self._required_env(name)
        try:
            return int(raw_value)
        except ValueError as exc:
            raise ValueError(f"{name} must be an integer") from exc
