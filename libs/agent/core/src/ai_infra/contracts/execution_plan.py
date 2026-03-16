"""Execution-plan contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from ai_infra.contracts.action_step import ActionStep
from ai_infra.contracts.step_dependency import StepDependency


@dataclass(frozen=True)
class ExecutionPlan:
    """Typed plan emitted by the planning service."""

    skill_name: str
    objective: str
    steps: tuple[ActionStep, ...]
    dependencies: tuple[StepDependency, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["steps"] = [step.to_dict() for step in self.steps]
        payload["dependencies"] = [dependency.to_dict() for dependency in self.dependencies]
        return payload
