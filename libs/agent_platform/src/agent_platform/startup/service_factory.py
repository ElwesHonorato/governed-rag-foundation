"""Service factory for the agent-platform MVP."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_infra.contracts.agent_run import AgentRun
from ai_infra.contracts.agent_session import AgentSession
from ai_infra.evaluation.offline_evaluation_runner import OfflineEvaluationRunner
from ai_infra.kernel.agent_session_manager import AgentSessionManager
from ai_infra.policies.capability_policy import CapabilityPolicy
from ai_infra.policies.sandbox_policy import SandboxPolicy
from ai_infra.policies.termination_policy import TerminationPolicy
from ai_infra.registry.capability_catalog import CapabilityCatalog
from ai_infra.registry.capability_registry import CapabilityRegistry
from ai_infra.runtime.execution_state_manager import ExecutionStateManager
from ai_infra.services.capability_execution_service import CapabilityExecutionService
from ai_infra.services.capability_planning_service import CapabilityPlanningService
from ai_infra.services.next_step_decider import NextStepDecider
from ai_infra.services.prompt_assembly_service import PromptAssemblyService
from ai_infra.services.response_validation_service import ResponseValidationService
from ai_infra.services.run_supervisor import RunSupervisor
from ai_infra.services.step_result_evaluation_service import StepResultEvaluationService
from agent_platform.infrastructure.bootstrap_vector_index import bootstrap_vector_index
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
from agent_platform.retrieval.weaviate_client import WeaviateRetrievalClient
from agent_platform.startup.contracts import AgentPlatformConfig
from agent_platform.startup.provider import SettingsProvider, SettingsRequest


@dataclass
class AgentPlatformApp:
    """Composition root for the MVP runtime."""

    capability_registry: CapabilityRegistry
    skill_registry: dict[str, dict[str, object]]
    session_store: LocalSessionStore
    run_store: LocalRunStore
    evaluation_runner: OfflineEvaluationRunner
    planning_service: CapabilityPlanningService
    session_manager: AgentSessionManager
    supervisor: RunSupervisor
    rag_service: RagService

    def run_objective(self, objective: str, skill_name: str) -> AgentRun:
        session = self.session_manager.create_session(objective=objective, skill_name=skill_name)
        plan = self.planning_service.build_plan(skill_name, objective, self.skill_registry[skill_name])
        run = self.supervisor.create_run(
            session_id=session.session_id,
            skill_name=skill_name,
            objective=objective,
            prompt_version="v1",
            execution_plan=plan,
        )
        session = self.session_manager.attach_run(session, run.run_id)
        completed_run = self.supervisor.run(run)
        self.session_manager.update_run_status(session, completed_run.run_id, completed_run.status)
        return completed_run


@dataclass(frozen=True)
class LocalStateStores:
    """File-backed stores rooted in the runtime state directory."""

    session_store: LocalSessionStore
    run_store: LocalRunStore
    checkpoint_store: LocalCheckpointStore


class AgentPlatformServiceFactory:
    """Builds the MVP service graph."""

    def build(self) -> AgentPlatformApp:
        settings = self._load_settings()
        index_path = self._ensure_vector_index(settings)
        capability_registry = self._build_capability_registry()
        skill_registry = load_skill_registry()
        stores = self._build_local_state_stores(settings)
        prompt_repository = LocalPromptRepository()
        planning_service = CapabilityPlanningService()
        execution_service = self._build_execution_service(
            settings=settings,
            index_path=index_path,
            prompt_repository=prompt_repository,
        )
        supervisor = self._build_supervisor(
            settings=settings,
            capability_registry=capability_registry,
            execution_service=execution_service,
            run_store=stores.run_store,
            checkpoint_store=stores.checkpoint_store,
        )
        rag_service = self._build_rag_service(settings)
        return AgentPlatformApp(
            capability_registry=capability_registry,
            skill_registry=skill_registry,
            session_store=stores.session_store,
            run_store=stores.run_store,
            evaluation_runner=OfflineEvaluationRunner(),
            planning_service=planning_service,
            session_manager=AgentSessionManager(stores.session_store),
            supervisor=supervisor,
            rag_service=rag_service,
        )

    def _load_settings(self) -> AgentPlatformConfig:
        settings = SettingsProvider(
            SettingsRequest(agent_platform=True)
        ).bundle.agent_platform
        if settings is None:
            raise ValueError("Agent platform settings were not requested")
        return settings

    def _ensure_vector_index(self, settings: AgentPlatformConfig) -> Path:
        state_dir = Path(settings.paths.state_dir)
        vector_fixture_dir = state_dir / "vector_fixture"
        vector_fixture_dir.mkdir(parents=True, exist_ok=True)
        index_path = vector_fixture_dir / "index.json"
        if not index_path.exists():
            bootstrap_vector_index(
                repo_root=settings.paths.repo_root,
                output_path=str(index_path),
                embedder=DeterministicEmbeddingFixture(),
            )
        return index_path

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
        index_path: Path,
        prompt_repository: LocalPromptRepository,
    ) -> CapabilityExecutionService:
        prompt_assembly_service = PromptAssemblyService(
            prompt_repository=prompt_repository
        )
        return CapabilityExecutionService(
            filesystem_gateway=LocalFilesystemAdapter(settings.paths.workspace_root),
            command_gateway=LocalCommandRunner(settings.paths.workspace_root),
            vector_gateway=LocalVectorSearch(
                str(index_path), DeterministicEmbeddingFixture()
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
