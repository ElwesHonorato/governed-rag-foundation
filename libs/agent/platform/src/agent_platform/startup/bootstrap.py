"""Runtime bootstrap steps for agent-platform."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_infra.retrieval.deterministic_retrieval_embedder import (
    DeterministicRetrievalEmbedder,
)
from agent_platform.startup.bootstrap_vector_index import bootstrap_vector_index
from agent_platform.startup.contracts import AgentPlatformConfig


@dataclass(frozen=True)
class PreparedRuntimeArtifacts:
    """Filesystem artifacts prepared before service wiring."""

    vector_index_path: Path


class RuntimeBootstrapper:
    """Prepare local runtime artifacts required by the service graph."""

    def bootstrap(
        self,
        settings: AgentPlatformConfig,
        retrieval_embedder: DeterministicRetrievalEmbedder,
    ) -> PreparedRuntimeArtifacts:
        self._ensure_vector_fixture_dir(settings)
        vector_index_path: Path = self._bootstrap_vector_index(
            settings,
            retrieval_embedder,
        )
        return PreparedRuntimeArtifacts(vector_index_path=vector_index_path)

    def _ensure_vector_fixture_dir(self, settings: AgentPlatformConfig) -> None:
        settings.paths.vector_fixture_dir.mkdir(parents=True, exist_ok=True)

    def _bootstrap_vector_index(
        self,
        settings: AgentPlatformConfig,
        retrieval_embedder: DeterministicRetrievalEmbedder,
    ) -> Path:
        vector_index_path = settings.paths.vector_index_path
        if not vector_index_path.exists():
            bootstrap_vector_index(
                workspace_root=str(settings.paths.workspace_root),
                output_path=str(vector_index_path),
                embedder=retrieval_embedder,
            )
        return vector_index_path
