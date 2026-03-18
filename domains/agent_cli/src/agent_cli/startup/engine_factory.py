"""Composition root for the agent CLI runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_infra.contracts.agent_run import AgentRun
from ai_infra.contracts.agent_session import AgentSession
from ai_infra.contracts.capability_descriptor import CapabilityDescriptor
from ai_infra.contracts.evaluation_run import EvaluationRun
from ai_infra.evaluation.offline_evaluation_runner import OfflineEvaluationRunner
from ai_infra.protocols.gateways.llm_gateway import LLMGateway
from ai_infra.registry.capability_registry import CapabilityRegistry
from ai_infra.retrieval.deterministic_hash_embedder import (
    DeterministicHashEmbedder,
)
from agent_platform.agent_runtime.execution_runtime_factory import (
    EngineGateways,
    ExecutionRuntimeFactory,
)
from agent_platform.agent_runtime.objective_runner import ObjectiveRunner
from agent_platform.gateways.retrieval.retrieval_gateway import RetrievalGateway
from agent_platform.agent_runtime.skill_registry import SkillRegistry
from agent_platform.gateways.state.local_run_store import LocalRunStore
from agent_platform.gateways.state.local_session_store import LocalSessionStore
from agent_platform.grounded_response.contracts import GroundedResponse
from agent_platform.grounded_response.grounded_response_factory import (
    GroundedResponseFactory,
)
from agent_platform.grounded_response.service import GroundedResponseService
from agent_platform.startup.bootstrap import PreparedRuntimeArtifacts, RuntimeBootstrapper
from agent_platform.startup.command_gateway_factory import CommandGatewayFactory
from agent_platform.startup.contracts import AgentPlatformConfig
from agent_platform.startup.filesystem_gateway_factory import FilesystemGatewayFactory
from agent_platform.startup.llm_gateway_factory import LLMGatewayFactory
from agent_platform.startup.local_state_stores_factory import (
    LocalStateStores,
    LocalStateStoresFactory,
)
from agent_platform.startup.packaged_configuration import (
    load_capability_catalog,
    load_skill_registry,
)
from agent_platform.startup.retrieval_gateway_factory import RetrievalGatewayFactory
from agent_platform.startup.vector_gateway_factory import VectorGatewayFactory


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


@dataclass(frozen=True)
class EngineStartupServices:
    """Startup-time collaborators for engine assembly."""

    bootstrapper: RuntimeBootstrapper
    retrieval_embedder: DeterministicHashEmbedder
    local_state_stores_factory: LocalStateStoresFactory


@dataclass(frozen=True)
class EngineGatewayFactories:
    """Gateway factories used by engine assembly."""

    filesystem: FilesystemGatewayFactory
    command: CommandGatewayFactory
    vector: VectorGatewayFactory
    llm: LLMGatewayFactory
    retrieval: RetrievalGatewayFactory


@dataclass(frozen=True)
class EngineRuntimeFactories:
    """Runtime factories used by engine assembly."""

    execution: ExecutionRuntimeFactory
    grounded_response: GroundedResponseFactory


class EngineFactory:
    """Build the agent CLI runtime graph."""

    def __init__(
        self,
        *,
        startup_services: EngineStartupServices,
        gateway_factories: EngineGatewayFactories,
        runtime_factories: EngineRuntimeFactories,
        settings: AgentPlatformConfig,
    ) -> None:
        self._startup_services = startup_services
        self._gateway_factories = gateway_factories
        self._runtime_factories = runtime_factories
        self._settings = settings
        self._runtime_settings: AgentPlatformConfig | None = None
        self._retrieval_embedder: DeterministicHashEmbedder | None = None
        self._vector_index_path: Path | None = None

    def build(self) -> Engine:
        retrieval_embedder: DeterministicHashEmbedder = (
            self._startup_services.retrieval_embedder
        )
        prepared_artifacts: PreparedRuntimeArtifacts = (
            self._startup_services.bootstrapper.bootstrap(
                self._settings,
                retrieval_embedder=retrieval_embedder,
            )
        )
        capability_registry: CapabilityRegistry = CapabilityRegistry(
            load_capability_catalog()
        )
        skill_registry: SkillRegistry = load_skill_registry()
        stores: LocalStateStores = self._startup_services.local_state_stores_factory.build(
            self._settings
        )
        self._runtime_settings = self._settings
        self._retrieval_embedder = retrieval_embedder
        self._vector_index_path = prepared_artifacts.vector_index_path
        gateways: EngineGateways = self._build_gateways()
        execution_runtime = self._runtime_factories.execution.build(
            self._settings,
            capability_registry,
            skill_registry,
            stores,
            gateways,
        )
        grounded_response_service: GroundedResponseService = (
            self._runtime_factories.grounded_response.build(
                self._settings,
                gateways,
            )
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

    def _build_gateways(self) -> EngineGateways:
        return EngineGateways(
            filesystem_gateway=self._gateway_factories.filesystem.build(
                self._runtime_settings
            ),
            command_gateway=self._gateway_factories.command.build(
                self._runtime_settings
            ),
            vector_gateway=self._gateway_factories.vector.build(
                vector_index_path=self._vector_index_path,
                retrieval_embedder=self._retrieval_embedder,
            ),
            llm_gateway=self._build_llm_gateway(),
            retrieval_gateway=self._build_retrieval_gateway(),
        )

    def _build_llm_gateway(self) -> LLMGateway:
        return self._gateway_factories.llm.build()

    def _build_retrieval_gateway(self) -> RetrievalGateway:
        return self._gateway_factories.retrieval.build()
