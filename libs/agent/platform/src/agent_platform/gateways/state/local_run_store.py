"""File-backed run store."""

from __future__ import annotations

import json
from pathlib import Path

from ai_infra.contracts.action_step import ActionStep
from ai_infra.contracts.agent_run import AgentRun
from ai_infra.contracts.capability_result import CapabilityResult
from ai_infra.contracts.execution_plan import ExecutionPlan


class LocalRunStore:
    """Persists run snapshots as JSON files."""

    def __init__(self, base_dir: str) -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def save_run(self, run: AgentRun) -> None:
        (self._base_dir / f"{run.run_id}.json").write_text(json.dumps(run.to_dict(), indent=2))

    def load_run(self, run_id: str) -> AgentRun:
        payload = json.loads((self._base_dir / f"{run_id}.json").read_text())
        plan = ExecutionPlan(
            skill_name=payload["execution_plan"]["skill_name"],
            objective=payload["execution_plan"]["objective"],
            steps=tuple(ActionStep(**step) for step in payload["execution_plan"]["steps"]),
        )
        results = tuple(CapabilityResult(**result) for result in payload.get("step_results", []))
        return AgentRun(
            run_id=payload["run_id"],
            session_id=payload["session_id"],
            skill_name=payload["skill_name"],
            objective=payload["objective"],
            status=payload["status"],
            prompt_version=payload["prompt_version"],
            execution_plan=plan,
            step_results=results,
            final_output=payload.get("final_output"),
            created_at=payload["created_at"],
            updated_at=payload["updated_at"],
        )
