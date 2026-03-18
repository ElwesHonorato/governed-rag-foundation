"""Domain-local runtime config assembly for the agent CLI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent_platform.startup.contracts import (
    AgentPlatformConfig,
    EmbedderParams,
    LLMParams,
    RetrievalParams,
    RuntimePaths,
)
from agent_settings.settings import SettingsBundle


@dataclass(frozen=True)
class StateDirectories:
    vector_fixture_dir: Path
    vector_index_path: Path
    sessions_dir: Path
    runs_dir: Path
    checkpoints_dir: Path


class AgentCliConfigFactory:
    """Build CLI runtime config from the centralized settings bundle."""

    def __init__(self, workspace_root: Path | None = None) -> None:
        self._workspace_root = workspace_root or Path(__file__).resolve().parent.parent

    def build(self, settings: SettingsBundle) -> AgentPlatformConfig:
        runtime_paths = self._resolve_local_paths()
        return AgentPlatformConfig(
            paths=runtime_paths,
            llm=LLMParams(
                llm_timeout_seconds=30,
            ),
            retrieval=RetrievalParams(
                retrieval_limit=5,
            ),
            embedder=EmbedderParams(
                embedding_dim=32,
            ),
        )

    def _resolve_local_paths(self) -> RuntimePaths:
        workspace_root = self._workspace_root
        state_dir = (workspace_root / ".agent_platform" / "localdata").resolve()
        state_directories = self._state_directories(state_dir)

        config_dir = (workspace_root / "config").resolve()
        vector_index_ignore_path = (config_dir / ".repositorylisterignore").resolve()
        state_dir.mkdir(parents=True, exist_ok=True)
        return RuntimePaths(
            workspace_root=workspace_root,
            vector_fixture_dir=state_directories.vector_fixture_dir,
            vector_index_path=state_directories.vector_index_path,
            vector_index_ignore_path=vector_index_ignore_path,
            sessions_dir=state_directories.sessions_dir,
            runs_dir=state_directories.runs_dir,
            checkpoints_dir=state_directories.checkpoints_dir,
        )

    def _state_directories(self, state_dir: Path) -> StateDirectories:
        return StateDirectories(
            vector_fixture_dir=(state_dir / "vector_fixture").resolve(),
            vector_index_path=((state_dir / "vector_fixture") / "index.json").resolve(),
            sessions_dir=(state_dir / "sessions").resolve(),
            runs_dir=(state_dir / "runs").resolve(),
            checkpoints_dir=(state_dir / "checkpoints").resolve(),
        )
