"""Next-step selection."""

from __future__ import annotations

from ai_infra.contracts.agent_run import AgentRun
from ai_infra.contracts.next_step_decision import NextStepDecision


class NextStepDecider:
    """Select the next unexecuted step."""

    def decide(self, run: AgentRun) -> NextStepDecision:
        completed = {result.step_id for result in run.step_results}
        for step in run.execution_plan.steps:
            if step.step_id not in completed:
                return NextStepDecision(step_id=step.step_id, reason="next_unfinished_step")
        return NextStepDecision(step_id=None, reason="plan_complete")
