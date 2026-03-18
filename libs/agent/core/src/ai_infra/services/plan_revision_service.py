"""Plan revision logic."""

from __future__ import annotations

from ai_infra.contracts.replan_decision import ReplanDecision


class PlanRevisionService:
    """MVP policy: do not automatically revise plans after failure."""

    def decide(self, can_continue: bool) -> ReplanDecision:
        if can_continue:
            return ReplanDecision(should_replan=False, reason="plan_can_continue")
        return ReplanDecision(should_replan=False, reason="mvp_does_not_replan")
