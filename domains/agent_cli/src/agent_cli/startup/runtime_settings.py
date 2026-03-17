"""Domain-local runtime config assembly for the agent CLI."""

from __future__ import annotations

from pathlib import Path

from agent_platform.startup.contracts import AgentPlatformConfig, RuntimePaths
from agent_settings.settings import SettingsBundle


class AgentCliConfigFactory:
    """Build CLI runtime config from the centralized settings bundle."""

    def __init__(self, workspace_root: Path | None = None) -> None:
        self._workspace_root = workspace_root or Path(__file__).resolve().parent.parent

    def build(self, settings: SettingsBundle) -> AgentPlatformConfig:
        runtime_paths = self._resolve_local_paths()
        return AgentPlatformConfig(
            paths=runtime_paths,
            llm=settings.llm,
            retrieval=settings.retrieval,
        )

    def _resolve_local_paths(self) -> RuntimePaths:
        workspace_root = self._workspace_root
        state_dir = (workspace_root / ".agent_platform" / "localdata").resolve()
        vector_fixture_dir = (state_dir / "vector_fixture").resolve()
        vector_index_path = (vector_fixture_dir / "index.json").resolve()
        vector_index_ignore_path = (
            workspace_root
            / "config"
            / ".repositorylisterignore"
        ).resolve()
        sessions_dir = (state_dir / "sessions").resolve()
        runs_dir = (state_dir / "runs").resolve()
        checkpoints_dir = (state_dir / "checkpoints").resolve()
        state_dir.mkdir(parents=True, exist_ok=True)
        return RuntimePaths(
            workspace_root=workspace_root,
            state_dir=state_dir,
            vector_fixture_dir=vector_fixture_dir,
            vector_index_path=vector_index_path,
            vector_index_ignore_path=vector_index_ignore_path,
            sessions_dir=sessions_dir,
            runs_dir=runs_dir,
            checkpoints_dir=checkpoints_dir,
        )
