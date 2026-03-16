"""Startup settings loading for the local agent-platform runtime."""

from __future__ import annotations

from pathlib import Path

from agent_settings.settings import (
    EnvironmentSettingsProvider,
    SettingsRequest,
    SettingsProvider,
)
from agent_platform.startup.contracts import (
    AgentPlatformConfig,
    RuntimePaths,
)

class AgentPlatformSettingsProvider(SettingsProvider[AgentPlatformConfig]):
    """Load requested startup settings from process environment."""

    def load(self) -> AgentPlatformConfig:
        provider = EnvironmentSettingsProvider(
            SettingsRequest(llm=True, retrieval=True)
        )
        workspace_root, state_dir = self._resolve_local_paths()
        return AgentPlatformConfig(
            paths=RuntimePaths(
                workspace_root=str(workspace_root),
                state_dir=str(state_dir),
            ),
            llm=provider.require_llm(),
            retrieval=provider.require_retrieval(),
        )

    def _resolve_local_paths(self) -> tuple[Path, Path]:
        workspace_root = Path.cwd().resolve()
        state_dir = (workspace_root / ".agent_platform" / "localdata").resolve()
        state_dir.mkdir(parents=True, exist_ok=True)
        return workspace_root, state_dir
