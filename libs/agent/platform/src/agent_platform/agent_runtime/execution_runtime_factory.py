"""Execution runtime assembly for the agent-platform engine."""

from __future__ import annotations

from dataclasses import dataclass

from ai_infra.protocols.gateways.llm_gateway import LLMGateway
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
from agent_platform.agent_runtime.objective_runner import ObjectiveRunner
from agent_platform.gateways.prompts.local_prompt_repository import (
    LocalPromptRepository,
)
from agent_platform.gateways.command.local_command_gateway import LocalCommandGateway
from agent_platform.gateways.filesystem.local_filesystem_gateway import (
    LocalFilesystemGateway,
)
from agent_platform.gateways.retrieval.local_vector_search import (
    LocalVectorSearchGateway,
)
from agent_platform.gateways.retrieval.retrieval_gateway import RetrievalGateway
from agent_platform.agent_runtime.skill_registry import SkillRegistry
from agent_platform.startup.contracts import AgentPlatformConfig
from agent_platform.startup.local_state_stores_factory import LocalStateStores
from ai_infra.registry.capability_registry import CapabilityRegistry


@dataclass(frozen=True)
class ExecutionRuntime:
    """Execution-side runtime collaborators exposed to the engine."""

    objective_runner: ObjectiveRunner
    evaluation_runner: OfflineEvaluationRunner


@dataclass(frozen=True)
class EngineGateways:
    """Concrete gateway instances shared across engine assembly."""

    filesystem_gateway: LocalFilesystemGateway
    command_gateway: LocalCommandGateway
    vector_gateway: LocalVectorSearchGateway
    llm_gateway: LLMGateway
    retrieval_gateway: RetrievalGateway


class ExecutionRuntimeFactory:
    """Build execution and supervision collaborators for the engine."""

    def build(
        self,
        settings: AgentPlatformConfig,
        capability_registry: CapabilityRegistry,
        skill_registry: SkillRegistry,
        stores: LocalStateStores,
        gateways: EngineGateways,
    ) -> ExecutionRuntime:
        planning_service = CapabilityPlanningService()
        session_manager = AgentSessionManager(stores.session_store)
        execution_service = self._build_execution_service(
            gateways,
            llm_model=settings.llm.llm_model,
        )
        supervisor = self._build_supervisor(
            settings,
            capability_registry,
            stores,
            execution_service,
        )
        return ExecutionRuntime(
            objective_runner=ObjectiveRunner(
                session_manager=session_manager,
                planning_service=planning_service,
                supervisor=supervisor,
                skill_registry=skill_registry,
            ),
            evaluation_runner=OfflineEvaluationRunner(),
        )

    def _build_execution_service(
        self,
        gateways: EngineGateways,
        *,
        llm_model: str,
    ) -> CapabilityExecutionService:
        prompt_repository = LocalPromptRepository()
        prompt_assembly_service = PromptAssemblyService(
            prompt_repository=prompt_repository
        )
        return CapabilityExecutionService(
            filesystem_gateway=gateways.filesystem_gateway,
            command_gateway=gateways.command_gateway,
            vector_gateway=gateways.vector_gateway,
            llm_gateway=gateways.llm_gateway,
            llm_model=llm_model,
            prompt_assembly_service=prompt_assembly_service,
        )

    def _build_supervisor(
        self,
        settings: AgentPlatformConfig,
        capability_registry: CapabilityRegistry,
        stores: LocalStateStores,
        execution_service: CapabilityExecutionService,
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
            run_manager=stores.run_store,
            checkpoint_manager=stores.checkpoint_store,
        )
