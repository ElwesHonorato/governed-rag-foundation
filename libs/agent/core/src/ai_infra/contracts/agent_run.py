"""Run-level contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from ai_infra.contracts.capability_result import CapabilityResult
from ai_infra.contracts.execution_plan import ExecutionPlan


@dataclass(frozen=True)
class AgentRun:
    """Persisted execution record for a supervised run."""

    run_id: str
    session_id: str
    skill_name: str
    objective: str
    status: str
    prompt_version: str
    execution_plan: ExecutionPlan
    step_results: tuple[CapabilityResult, ...] = field(default_factory=tuple)
    final_output: str | None = None
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["execution_plan"] = self.execution_plan.to_dict()
        payload["step_results"] = [result.to_dict() for result in self.step_results]
        return payload
