"""Execution-state helpers."""

from __future__ import annotations

from ai_infra.contracts.agent_run import AgentRun
from ai_infra.contracts.capability_result import CapabilityResult


class ExecutionStateManager:
    """Updates run state after step execution."""

    def add_step_result(self, run: AgentRun, result: CapabilityResult) -> AgentRun:
        final_output = run.final_output
        if result.capability_name == "llm_synthesize" and result.success:
            final_output = str(result.output.get("text", ""))
        status = "running"
        if final_output:
            status = "completed"
        if not result.success:
            status = "failed"
        return AgentRun(
            run_id=run.run_id,
            session_id=run.session_id,
            skill_name=run.skill_name,
            objective=run.objective,
            status=status,
            prompt_version=run.prompt_version,
            execution_plan=run.execution_plan,
            step_results=tuple(list(run.step_results) + [result]),
            final_output=final_output,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )
