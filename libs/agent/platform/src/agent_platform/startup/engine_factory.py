"""Composition root for the local agent-platform runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_infra.contracts.agent_run import AgentRun
from ai_infra.contracts.agent_session import AgentSession
from ai_infra.contracts.capability_descriptor import CapabilityDescriptor
from ai_infra.contracts.evaluation_run import EvaluationRun
from ai_infra.evaluation.offline_evaluation_runner import OfflineEvaluationRunner
from ai_infra.registry.capability_registry import CapabilityRegistry
from ai_infra.retrieval.deterministic_retrieval_embedder import (
    DeterministicRetrievalEmbedder,
)
from agent_platform.clients.llm.ollama_client import OllamaClient
from agent_platform.clients.retrieval.weaviate_client import WeaviateClient
from agent_platform.agent_runtime.objective_runner import ObjectiveRunner
from agent_platform.startup.contracts import AgentPlatformConfig
from agent_platform.agent_runtime.execution_runtime_factory import (
    EngineGateways,
    ExecutionRuntimeFactory,
)
from agent_platform.agent_runtime.skill_registry import SkillRegistry
from agent_platform.grounded_response.contracts import GroundedResponse
from agent_platform.grounded_response.grounded_response_factory import (
    GroundedResponseFactory,
)
from agent_platform.grounded_response.service import GroundedResponseService
from agent_platform.gateways.command.local_command_gateway import LocalCommandGateway
from agent_platform.gateways.filesystem.local_filesystem_gateway import (
    LocalFilesystemGateway,
)
from agent_platform.gateways.llm.llm_gateway import LLMGateway
from agent_platform.gateways.retrieval.local_vector_search import (
    LocalVectorSearchGateway,
)
from agent_platform.gateways.retrieval.retrieval_gateway import RetrievalGateway
from agent_platform.gateways.state.local_run_store import LocalRunStore
from agent_platform.gateways.state.local_session_store import LocalSessionStore
from agent_platform.startup.bootstrap import RuntimeBootstrapper
from agent_platform.startup.local_state_stores_factory import LocalStateStoresFactory
from agent_platform.startup.packaged_configuration import (
    load_capability_catalog,
    load_skill_registry,
)
from agent_platform.startup.retrieval_embedder_factory import (
    RetrievalEmbedderFactory,
)
from agent_platform.startup.retrieval_composition import RetrievalComposition
from agent_platform.startup.runtime_settings import AgentPlatformConfigFactory
from agent_settings.settings import SettingsBundle


@dataclass(frozen=True)
class Engine:
    """Narrow application-facing runtime boundary."""

    _capability_registry: CapabilityRegistry
    _skill_registry: SkillRegistry
    _session_store: LocalSessionStore
    _run_store: LocalRunStore
    _evaluation_runner: OfflineEvaluationRunner
    _objective_runner: ObjectiveRunner
    _grounded_response_service: GroundedResponseService

    def list_capabilities(self) -> list[CapabilityDescriptor]:
        return self._capability_registry.list_capabilities()

    def list_skills(self) -> list[str]:
        return self._skill_registry.names()

    def load_session(self, session_id: str) -> AgentSession:
        return self._session_store.load_session(session_id)

    def load_run(self, run_id: str) -> AgentRun:
        return self._run_store.load_run(run_id)

    def evaluate_run(self, run_id: str) -> EvaluationRun:
        return self._evaluation_runner.evaluate(self.load_run(run_id))

    def query_grounded_response(self, body: dict[str, object]) -> GroundedResponse:
        return self._grounded_response_service.respond(body)

    def run_objective(self, objective: str, skill_name: str) -> AgentRun:
        return self._objective_runner.run(objective=objective, skill_name=skill_name)


class EngineFactory:
    """Build the local runtime graph for agent-platform."""

    def __init__(
        self,
        *,
        bootstrapper: RuntimeBootstrapper,
        retrieval_embedder_factory: RetrievalEmbedderFactory,
        local_state_stores_factory: LocalStateStoresFactory,
        settings: SettingsBundle,
        execution_runtime_factory: ExecutionRuntimeFactory,
        grounded_response_factory: GroundedResponseFactory,
    ) -> None:
        self._bootstrapper = bootstrapper
        self._retrieval_embedder_factory = retrieval_embedder_factory
        self._local_state_stores_factory = local_state_stores_factory
        self._settings = settings
        self._execution_runtime_factory = execution_runtime_factory
        self._grounded_response_factory = grounded_response_factory

    def build(self) -> Engine:
        settings: AgentPlatformConfig = AgentPlatformConfigFactory().build(self._settings)
        retrieval_embedder = self._retrieval_embedder_factory.build(
            self._settings.retrieval.embedding_dim
        )
        prepared_artifacts = self._bootstrapper.prepare(
            settings,
            retrieval=RetrievalComposition(embedder=retrieval_embedder),
        )
        capability_registry = CapabilityRegistry(load_capability_catalog())
        skill_registry = load_skill_registry()
        stores = self._local_state_stores_factory.build(settings)
        gateways = self._build_gateways(
            settings=settings,
            retrieval_embedder=retrieval_embedder,
            vector_index_path=prepared_artifacts.vector_index_path,
        )
        execution_runtime = self._execution_runtime_factory.build(
            settings,
            capability_registry,
            skill_registry,
            stores,
            gateways,
        )
        grounded_response_service = self._grounded_response_factory.build(
            settings,
            gateways,
        )
        return Engine(
            _capability_registry=capability_registry,
            _skill_registry=skill_registry,
            _session_store=stores.session_store,
            _run_store=stores.run_store,
            _evaluation_runner=execution_runtime.evaluation_runner,
            _objective_runner=execution_runtime.objective_runner,
            _grounded_response_service=grounded_response_service,
        )

    def _build_gateways(
        self,
        *,
        settings: AgentPlatformConfig,
        retrieval_embedder: DeterministicRetrievalEmbedder,
        vector_index_path: Path,
    ) -> EngineGateways:
        llm_client = OllamaClient(
            llm_url=settings.llm.llm_url,
            timeout_seconds=settings.llm.llm_timeout_seconds,
        )
        retrieval_client = WeaviateClient(
            weaviate_url=settings.retrieval.weaviate_url,
            embedder=retrieval_embedder,
        )
        return EngineGateways(
            filesystem_gateway=LocalFilesystemGateway(str(settings.paths.workspace_root)),
            command_gateway=LocalCommandGateway(str(settings.paths.workspace_root)),
            vector_gateway=LocalVectorSearchGateway(
                str(vector_index_path),
                retrieval_embedder,
            ),
            llm_gateway=LLMGateway(client=llm_client),
            retrieval_gateway=RetrievalGateway(client=retrieval_client),
        )
