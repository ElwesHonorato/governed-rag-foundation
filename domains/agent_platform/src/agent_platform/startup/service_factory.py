"""Service factory for the agent-platform MVP."""

from __future__ import annotations

import json
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
from agent_platform.infrastructure.local_capability_catalog import load_skill_registry
from agent_platform.infrastructure.local_checkpoint_store import LocalCheckpointStore
from agent_platform.infrastructure.local_command_runner import LocalCommandRunner
from agent_platform.infrastructure.local_embedding_fixture import DeterministicEmbeddingFixture
from agent_platform.infrastructure.local_filesystem_adapter import LocalFilesystemAdapter
from agent_platform.infrastructure.local_model_gateway import LocalModelGateway
from agent_platform.infrastructure.local_prompt_repository import LocalPromptRepository
from agent_platform.infrastructure.local_run_store import LocalRunStore
from agent_platform.infrastructure.local_session_store import LocalSessionStore
from agent_platform.infrastructure.local_vector_search import LocalVectorSearch
from agent_platform.startup.config_extractor import AgentPlatformConfigExtractor


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


class AgentPlatformServiceFactory:
    """Builds the MVP service graph."""

    def build(self) -> AgentPlatformApp:
        config = AgentPlatformConfigExtractor().extract()
        config_dir = Path(config.config_dir)
        state_dir = Path(config.state_dir)
        vector_fixture_dir = state_dir / "vector_fixture"
        vector_fixture_dir.mkdir(parents=True, exist_ok=True)
        index_path = vector_fixture_dir / "index.json"
        if not index_path.exists():
            bootstrap_vector_index(
                repo_root=config.repo_root,
                output_path=str(index_path),
                embedder=DeterministicEmbeddingFixture(),
            )

        capability_registry = CapabilityRegistry(
            CapabilityCatalog(str(config_dir / "capabilities.yaml"))
        )
        skill_registry = load_skill_registry(str(config_dir / "skills.yaml"))
        session_store = LocalSessionStore(str(state_dir / "sessions"))
        run_store = LocalRunStore(str(state_dir / "runs"))
        checkpoint_store = LocalCheckpointStore(str(state_dir / "checkpoints"))
        prompt_repository = LocalPromptRepository(str(config_dir / "prompts"))
        planning_service = CapabilityPlanningService()
        prompt_assembly_service = PromptAssemblyService(prompt_repository=prompt_repository)
        execution_service = CapabilityExecutionService(
            filesystem_gateway=LocalFilesystemAdapter(config.workspace_root),
            command_gateway=LocalCommandRunner(config.workspace_root),
            vector_gateway=LocalVectorSearch(str(index_path), DeterministicEmbeddingFixture()),
            model_gateway=LocalModelGateway(),
            prompt_assembly_service=prompt_assembly_service,
        )
        supervisor = RunSupervisor(
            registry=capability_registry,
            capability_policy=CapabilityPolicy(),
            sandbox_policy=SandboxPolicy(config.workspace_root),
            termination_policy=TerminationPolicy(),
            execution_service=execution_service,
            next_step_decider=NextStepDecider(),
            state_manager=ExecutionStateManager(),
            response_validator=ResponseValidationService(),
            step_evaluator=StepResultEvaluationService(),
            run_manager=run_store,
            checkpoint_manager=checkpoint_store,
        )
        return AgentPlatformApp(
            capability_registry=capability_registry,
            skill_registry=skill_registry,
            session_store=session_store,
            run_store=run_store,
            evaluation_runner=OfflineEvaluationRunner(),
            planning_service=planning_service,
            session_manager=AgentSessionManager(session_store),
            supervisor=supervisor,
        )
