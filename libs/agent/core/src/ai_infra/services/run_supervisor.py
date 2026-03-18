"""Supervised runtime loop."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from ai_infra.contracts.agent_run import AgentRun
from ai_infra.contracts.capability_request import CapabilityRequest
from ai_infra.contracts.session_checkpoint import SessionCheckpoint
from ai_infra.protocols.kernel.checkpoint_manager import CheckpointManager
from ai_infra.policies.capability_policy import CapabilityPolicy
from ai_infra.policies.sandbox_policy import SandboxPolicy
from ai_infra.policies.termination_policy import TerminationPolicy
from ai_infra.registry.capability_registry import CapabilityRegistry
from ai_infra.protocols.runtime.agent_run_manager import AgentRunManager
from ai_infra.runtime.execution_state_manager import ExecutionStateManager
from ai_infra.services.capability_execution_service import CapabilityExecutionService
from ai_infra.services.next_step_decider import NextStepDecider
from ai_infra.services.response_validation_service import ResponseValidationService
from ai_infra.services.step_result_evaluation_service import StepResultEvaluationService


class RunSupervisor:
    """Runs a plan step-by-step under platform control."""

    def __init__(
        self,
        registry: CapabilityRegistry,
        capability_policy: CapabilityPolicy,
        sandbox_policy: SandboxPolicy,
        termination_policy: TerminationPolicy,
        execution_service: CapabilityExecutionService,
        next_step_decider: NextStepDecider,
        state_manager: ExecutionStateManager,
        response_validator: ResponseValidationService,
        step_evaluator: StepResultEvaluationService,
        run_manager: AgentRunManager,
        checkpoint_manager: CheckpointManager,
    ) -> None:
        self._registry = registry
        self._capability_policy = capability_policy
        self._sandbox_policy = sandbox_policy
        self._termination_policy = termination_policy
        self._execution_service = execution_service
        self._next_step_decider = next_step_decider
        self._state_manager = state_manager
        self._response_validator = response_validator
        self._step_evaluator = step_evaluator
        self._run_manager = run_manager
        self._checkpoint_manager = checkpoint_manager

    def create_run(self, session_id: str, skill_name: str, objective: str, prompt_version: str, execution_plan) -> AgentRun:
        timestamp = datetime.now(UTC).isoformat()
        return AgentRun(
            run_id=f"run-{uuid4().hex[:12]}",
            session_id=session_id,
            skill_name=skill_name,
            objective=objective,
            status="created",
            prompt_version=prompt_version,
            execution_plan=execution_plan,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def run(self, initial_run: AgentRun) -> AgentRun:
        run = replace(initial_run, status="running", updated_at=datetime.now(UTC).isoformat())
        self._run_manager.save_run(run)
        while True:
            self._termination_policy.validate(run)
            decision = self._next_step_decider.decide(run)
            if decision.step_id is None:
                run = replace(run, status="completed", updated_at=datetime.now(UTC).isoformat())
                self._run_manager.save_run(run)
                return run
            step = next(step for step in run.execution_plan.steps if step.step_id == decision.step_id)
            descriptor = self._registry.resolve(step.capability_name)
            self._capability_policy.validate(descriptor)
            if step.capability_name == "filesystem_read":
                self._sandbox_policy.validate_path(str(step.input_payload["path"]))
            if step.capability_name == "command_run_safe":
                self._sandbox_policy.validate_command(list(step.input_payload["command"]))
            request = CapabilityRequest(
                capability_name=step.capability_name,
                session_id=run.session_id,
                run_id=run.run_id,
                step_id=step.step_id,
                input_payload=step.input_payload,
            )
            result = self._execution_service.execute(request=request, run=run)
            self._response_validator.validate(result)
            run = replace(
                self._state_manager.add_step_result(run=run, result=result),
                updated_at=datetime.now(UTC).isoformat(),
            )
            self._run_manager.save_run(run)
            self._checkpoint_manager.save_checkpoint(
                SessionCheckpoint(
                    checkpoint_id=f"chk-{uuid4().hex[:12]}",
                    run_id=run.run_id,
                    session_id=run.session_id,
                    snapshot=run.to_dict(),
                    created_at=datetime.now(UTC).isoformat(),
                )
            )
            if not self._step_evaluator.is_successful(result):
                run = replace(run, status="failed", updated_at=datetime.now(UTC).isoformat())
                self._run_manager.save_run(run)
                return run
