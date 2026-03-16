"""Execution runtime assembly for the agent-platform engine."""

from __future__ import annotations

from dataclasses import dataclass

from ai_infra.evaluation.offline_evaluation_runner import OfflineEvaluationRunner
from ai_infra.kernel.agent_session_manager import AgentSessionManager
from ai_infra.policies.capability_policy import CapabilityPolicy
from ai_infra.policies.sandbox_policy import SandboxPolicy
from ai_infra.policies.termination_policy import TerminationPolicy
from ai_infra.runtime.execution_state_manager import ExecutionStateManager
from ai_infra.services.capability_execution_service import CapabilityExecutionService
from ai_infra.services.capability_planning_service import CapabilityPlanningService
from ai_infra.services.next_step_decider import NextStepDecider
from ai_infra.services.prompt_assembly_service import PromptAssemblyService
from ai_infra.services.response_validation_service import ResponseValidationService
from ai_infra.services.run_supervisor import RunSupervisor
from ai_infra.services.step_result_evaluation_service import StepResultEvaluationService
from agent_platform.application.objective_runner import ObjectiveRunner
from agent_platform.infrastructure.local_embedding_fixture import DeterministicEmbeddingFixture
from agent_platform.gateways.command.local_command_gateway import LocalCommandGateway
from agent_platform.gateways.filesystem.local_filesystem_gateway import (
    LocalFilesystemGateway,
)
from agent_platform.gateways.llm.local_model_gateway import LocalModelGateway
from agent_platform.gateways.prompts.local_prompt_repository import (
    LocalPromptRepository,
)
from agent_platform.gateways.retrieval.local_vector_search import LocalVectorSearch
from agent_platform.startup.startup_assets_factory import StartupAssets


@dataclass(frozen=True)
class ExecutionRuntime:
    """Execution-side runtime collaborators exposed to the engine."""

    objective_runner: ObjectiveRunner
    evaluation_runner: OfflineEvaluationRunner


class ExecutionRuntimeFactory:
    """Build execution and supervision collaborators for the engine."""

    def build(self, assets: StartupAssets) -> ExecutionRuntime:
        planning_service = CapabilityPlanningService()
        session_manager = AgentSessionManager(assets.stores.session_store)
        execution_service = self._build_execution_service(assets)
        supervisor = self._build_supervisor(assets, execution_service)
        return ExecutionRuntime(
            objective_runner=ObjectiveRunner(
                session_manager=session_manager,
                planning_service=planning_service,
                supervisor=supervisor,
                skill_registry=assets.skill_registry,
            ),
            evaluation_runner=OfflineEvaluationRunner(),
        )

    def _build_execution_service(
        self, assets: StartupAssets
    ) -> CapabilityExecutionService:
        prompt_repository = LocalPromptRepository()
        prompt_assembly_service = PromptAssemblyService(
            prompt_repository=prompt_repository
        )
        settings = assets.settings
        return CapabilityExecutionService(
            filesystem_gateway=LocalFilesystemGateway(settings.paths.workspace_root),
            command_gateway=LocalCommandGateway(settings.paths.workspace_root),
            vector_gateway=LocalVectorSearch(
                str(assets.prepared_artifacts.vector_index_path),
                DeterministicEmbeddingFixture(),
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
        assets: StartupAssets,
        execution_service: CapabilityExecutionService,
    ) -> RunSupervisor:
        settings = assets.settings
        return RunSupervisor(
            registry=assets.capability_registry,
            capability_policy=CapabilityPolicy(),
            sandbox_policy=SandboxPolicy(settings.paths.workspace_root),
            termination_policy=TerminationPolicy(),
            execution_service=execution_service,
            next_step_decider=NextStepDecider(),
            state_manager=ExecutionStateManager(),
            response_validator=ResponseValidationService(),
            step_evaluator=StepResultEvaluationService(),
            run_manager=assets.stores.run_store,
            checkpoint_manager=assets.stores.checkpoint_store,
        )
