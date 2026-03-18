"""Offline evaluation runner."""

from __future__ import annotations

from ai_infra.contracts.agent_run import AgentRun
from ai_infra.contracts.evaluation_run import EvaluationRun


class OfflineEvaluationRunner:
    """Scores captured runs using lightweight MVP checks."""

    def evaluate(self, run: AgentRun) -> EvaluationRun:
        checks = {
            "completed": run.status == "completed",
            "has_final_output": bool((run.final_output or "").strip()),
            "has_step_results": bool(run.step_results),
        }
        notes = ()
        if not checks["completed"]:
            notes = ("run_did_not_complete",)
        return EvaluationRun(run_id=run.run_id, success=all(checks.values()), checks=checks, notes=notes)
