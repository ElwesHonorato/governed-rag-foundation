"""Platform config assembly from a centralized settings bundle."""

from __future__ import annotations

from pathlib import Path

from agent_settings.settings import (
    SettingsBundle,
)
from agent_platform.startup.contracts import (
    AgentPlatformConfig,
    RuntimePaths,
)


class AgentPlatformConfigFactory:
    """Build agent-platform config from a centralized settings bundle."""

    def build(self, settings: SettingsBundle) -> AgentPlatformConfig:
        runtime_paths = self._resolve_local_paths()
        return AgentPlatformConfig(
            paths=runtime_paths,
            llm=settings.llm,
            retrieval=settings.retrieval,
        )

    def _resolve_local_paths(self) -> RuntimePaths:
        workspace_root = Path.cwd().resolve()
        state_dir = (workspace_root / ".agent_platform" / "localdata").resolve()
        vector_fixture_dir = (state_dir / "vector_fixture").resolve()
        vector_index_path = (vector_fixture_dir / "index.json").resolve()
        sessions_dir = (state_dir / "sessions").resolve()
        runs_dir = (state_dir / "runs").resolve()
        checkpoints_dir = (state_dir / "checkpoints").resolve()
        state_dir.mkdir(parents=True, exist_ok=True)
        return RuntimePaths(
            workspace_root=workspace_root,
            state_dir=state_dir,
            vector_fixture_dir=vector_fixture_dir,
            vector_index_path=vector_index_path,
            sessions_dir=sessions_dir,
            runs_dir=runs_dir,
            checkpoints_dir=checkpoints_dir,
        )
