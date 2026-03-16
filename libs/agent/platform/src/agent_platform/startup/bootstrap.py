"""Runtime bootstrap steps for agent-platform."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent_platform.startup.bootstrap_vector_index import bootstrap_vector_index
from agent_platform.startup.contracts import AgentPlatformConfig
from agent_platform.startup.retrieval_composition import RetrievalComposition


@dataclass(frozen=True)
class PreparedRuntimeArtifacts:
    """Filesystem artifacts prepared before service wiring."""

    vector_index_path: Path


class RuntimeBootstrapper:
    """Prepare local runtime artifacts required by the service graph."""

    def prepare(
        self,
        settings: AgentPlatformConfig,
        retrieval: RetrievalComposition,
    ) -> PreparedRuntimeArtifacts:
        state_dir = Path(settings.paths.state_dir)
        vector_fixture_dir = state_dir / "vector_fixture"
        vector_fixture_dir.mkdir(parents=True, exist_ok=True)
        index_path = vector_fixture_dir / "index.json"
        if not index_path.exists():
            bootstrap_vector_index(
                workspace_root=settings.paths.workspace_root,
                output_path=str(index_path),
                embedder=retrieval.embedder,
            )
        return PreparedRuntimeArtifacts(vector_index_path=index_path)
