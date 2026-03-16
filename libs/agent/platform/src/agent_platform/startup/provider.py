"""Startup settings provider for agent-platform."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from agent_platform.startup.contracts import (
    AgentPlatformConfig,
    LLMSettings,
    RepositoryPaths,
    RetrievalSettings,
)


@dataclass(frozen=True)
class SettingsRequest:
    """Requested startup settings to load."""

    agent_platform: bool = False


@dataclass(frozen=True)
class SettingsBundle:
    """Bundle of loaded startup settings."""

    agent_platform: AgentPlatformConfig | None = None


def load_agent_platform_config() -> AgentPlatformConfig:
    """Load agent-platform startup configuration."""
    workspace_root, state_dir = _resolve_local_paths()
    return AgentPlatformConfig(
        paths=RepositoryPaths(
            repo_root=str(workspace_root),
            workspace_root=str(workspace_root),
            state_dir=str(state_dir),
        ),
        llm=LLMSettings(
            llm_url=_required_env("LLM_URL"),
            llm_model=_required_env("LLM_MODEL"),
            llm_timeout_seconds=_required_int_env("LLM_TIMEOUT_SECONDS"),
        ),
        retrieval=RetrievalSettings(
            weaviate_url=_required_env("WEAVIATE_URL"),
            embedding_dim=_required_int_env("EMBEDDING_DIM"),
            retrieval_limit=int(os.environ.get("WEAVIATE_QUERY_DEFAULTS_LIMIT", "5")),
        ),
    )


class SettingsProvider:
    """Load requested startup settings from process environment."""

    def __init__(self, request: SettingsRequest) -> None:
        self._request = request

    @property
    def agent_platform(self) -> AgentPlatformConfig | None:
        if not self._request.agent_platform:
            return None
        return load_agent_platform_config()

    @property
    def bundle(self) -> SettingsBundle:
        return SettingsBundle(agent_platform=self.agent_platform)


def _resolve_local_paths() -> tuple[Path, Path]:
    workspace_root = Path.cwd().resolve()
    state_dir = (workspace_root / ".agent_platform" / "localdata").resolve()
    state_dir.mkdir(parents=True, exist_ok=True)
    return workspace_root, state_dir


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"{name} is not configured")
    return value.strip()


def _required_int_env(name: str) -> int:
    raw_value = _required_env(name)
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
