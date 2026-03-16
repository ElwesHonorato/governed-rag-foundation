"""Composition root for the local agent-platform runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_infra.contracts.agent_run import AgentRun
from ai_infra.contracts.agent_session import AgentSession
from ai_infra.contracts.capability_descriptor import CapabilityDescriptor
from ai_infra.contracts.evaluation_run import EvaluationRun
from ai_infra.evaluation.offline_evaluation_runner import OfflineEvaluationRunner
from ai_infra.kernel.agent_session_manager import AgentSessionManager
from ai_infra.policies.capability_policy import CapabilityPolicy
from ai_infra.policies.sandbox_policy import SandboxPolicy
from ai_infra.policies.termination_policy import TerminationPolicy
from ai_infra.registry.capability_registry import CapabilityRegistry
from ai_infra.runtime.execution_state_manager import ExecutionStateManager
from ai_infra.services.capability_execution_service import CapabilityExecutionService
from ai_infra.services.capability_planning_service import CapabilityPlanningService
from ai_infra.services.next_step_decider import NextStepDecider
from ai_infra.services.prompt_assembly_service import PromptAssemblyService
from ai_infra.services.response_validation_service import ResponseValidationService
from ai_infra.services.run_supervisor import RunSupervisor
from ai_infra.services.step_result_evaluation_service import StepResultEvaluationService
from agent_platform.application.objective_runner import ObjectiveRunner
from agent_platform.application.skill_registry import SkillRegistry
from agent_platform.infrastructure.local_capability_catalog import (
    load_capability_catalog,
    load_skill_registry,
)
from agent_platform.infrastructure.local_checkpoint_store import LocalCheckpointStore
from agent_platform.infrastructure.local_command_runner import LocalCommandRunner
from agent_platform.infrastructure.local_embedding_fixture import DeterministicEmbeddingFixture
from agent_platform.infrastructure.local_filesystem_adapter import LocalFilesystemAdapter
from agent_platform.infrastructure.local_model_gateway import LocalModelGateway
from agent_platform.infrastructure.local_prompt_repository import LocalPromptRepository
from agent_platform.infrastructure.local_run_store import LocalRunStore
from agent_platform.infrastructure.local_session_store import LocalSessionStore
from agent_platform.infrastructure.local_vector_search import LocalVectorSearch
from agent_platform.llm.ollama_client import OllamaClient
from agent_platform.rag.service import RagService
from agent_platform.rag.contracts import RagResponse
from agent_platform.retrieval.weaviate_client import WeaviateRetrievalClient
from agent_platform.startup.bootstrap import PreparedRuntimeArtifacts, RuntimeBootstrapper
from agent_platform.startup.contracts import AgentPlatformConfig
from agent_platform.startup.provider import SettingsProvider, SettingsRequest


@dataclass(frozen=True)
class AgentPlatformRuntime:
    """Narrow application-facing runtime boundary."""

    _capability_registry: CapabilityRegistry
    _skill_registry: SkillRegistry
    _session_store: LocalSessionStore
    _run_store: LocalRunStore
    _evaluation_runner: OfflineEvaluationRunner
    _objective_runner: ObjectiveRunner
    _rag_service: RagService

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

    def query_rag(self, body: dict[str, object]) -> RagResponse:
        return self._rag_service.respond(body)

    def run_objective(self, objective: str, skill_name: str) -> AgentRun:
        return self._objective_runner.run(objective=objective, skill_name=skill_name)


@dataclass(frozen=True)
class LocalStateStores:
    """File-backed stores rooted in the runtime state directory."""

    session_store: LocalSessionStore
    run_store: LocalRunStore
    checkpoint_store: LocalCheckpointStore


class AgentPlatformServiceFactory:
    """Build the local runtime graph for agent-platform."""

    def __init__(self, bootstrapper: RuntimeBootstrapper | None = None) -> None:
        self._bootstrapper = bootstrapper or RuntimeBootstrapper()

    def build(self) -> AgentPlatformRuntime:
        settings = self._load_settings()
        artifacts = self._bootstrapper.prepare(settings)
        capability_registry = self._build_capability_registry()
        skill_registry = load_skill_registry()
        stores = self._build_local_state_stores(settings)
        planning_service = CapabilityPlanningService()
        session_manager = AgentSessionManager(stores.session_store)
        execution_service = self._build_execution_service(
            settings=settings,
            artifacts=artifacts,
        )
        supervisor = self._build_supervisor(
            settings=settings,
            capability_registry=capability_registry,
            execution_service=execution_service,
            run_store=stores.run_store,
            checkpoint_store=stores.checkpoint_store,
        )
        objective_runner = ObjectiveRunner(
            session_manager=session_manager,
            planning_service=planning_service,
            supervisor=supervisor,
            skill_registry=skill_registry,
        )
        rag_service = self._build_rag_service(settings)
        return AgentPlatformRuntime(
            _capability_registry=capability_registry,
            _skill_registry=skill_registry,
            _session_store=stores.session_store,
            _run_store=stores.run_store,
            _evaluation_runner=OfflineEvaluationRunner(),
            _objective_runner=objective_runner,
            _rag_service=rag_service,
        )

    def _load_settings(self) -> AgentPlatformConfig:
        settings = SettingsProvider(
            SettingsRequest(agent_platform=True)
        ).bundle.agent_platform
        if settings is None:
            raise ValueError("Agent platform settings were not requested")
        return settings

    def _build_capability_registry(self) -> CapabilityRegistry:
        return CapabilityRegistry(load_capability_catalog())

    def _build_local_state_stores(
        self, settings: AgentPlatformConfig
    ) -> LocalStateStores:
        state_dir = Path(settings.paths.state_dir)
        return LocalStateStores(
            session_store=LocalSessionStore(str(state_dir / "sessions")),
            run_store=LocalRunStore(str(state_dir / "runs")),
            checkpoint_store=LocalCheckpointStore(str(state_dir / "checkpoints")),
        )

    def _build_execution_service(
        self,
        *,
        settings: AgentPlatformConfig,
        artifacts: PreparedRuntimeArtifacts,
    ) -> CapabilityExecutionService:
        prompt_repository = LocalPromptRepository()
        prompt_assembly_service = PromptAssemblyService(
            prompt_repository=prompt_repository
        )
        return CapabilityExecutionService(
            filesystem_gateway=LocalFilesystemAdapter(settings.paths.workspace_root),
            command_gateway=LocalCommandRunner(settings.paths.workspace_root),
            vector_gateway=LocalVectorSearch(
                str(artifacts.vector_index_path), DeterministicEmbeddingFixture()
            ),
            model_gateway=LocalModelGateway(
                llm_url=settings.llm.llm_url,
                llm_model=settings.llm.llm_model,
                timeout_seconds=settings.llm.llm_timeout_seconds,
            ),
            prompt_assembly_service=prompt_assembly_service,
        )

    def _build_supervisor(
        self,
        *,
        settings: AgentPlatformConfig,
        capability_registry: CapabilityRegistry,
        execution_service: CapabilityExecutionService,
        run_store: LocalRunStore,
        checkpoint_store: LocalCheckpointStore,
    ) -> RunSupervisor:
        return RunSupervisor(
            registry=capability_registry,
            capability_policy=CapabilityPolicy(),
            sandbox_policy=SandboxPolicy(settings.paths.workspace_root),
            termination_policy=TerminationPolicy(),
            execution_service=execution_service,
            next_step_decider=NextStepDecider(),
            state_manager=ExecutionStateManager(),
            response_validator=ResponseValidationService(),
            step_evaluator=StepResultEvaluationService(),
            run_manager=run_store,
            checkpoint_manager=checkpoint_store,
        )

    def _build_rag_service(self, settings: AgentPlatformConfig) -> RagService:
        return RagService(
            llm_client=OllamaClient(
                llm_url=settings.llm.llm_url,
                timeout_seconds=settings.llm.llm_timeout_seconds,
            ),
            retrieval_client=WeaviateRetrievalClient(
                weaviate_url=settings.retrieval.weaviate_url,
                embedding_dim=settings.retrieval.embedding_dim,
            ),
            model=settings.llm.llm_model,
            retrieval_limit=settings.retrieval.retrieval_limit,
        )
