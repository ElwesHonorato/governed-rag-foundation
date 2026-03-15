"""Planning service for the MVP skills."""

from __future__ import annotations

from ai_infra.contracts.action_step import ActionStep
from ai_infra.contracts.execution_plan import ExecutionPlan


class CapabilityPlanningService:
    """Builds deterministic plans for the MVP skills."""

    def build_plan(self, skill_name: str, objective: str, skill_config: dict[str, object]) -> ExecutionPlan:
        raw_steps = skill_config["steps"]
        steps = []
        for index, item in enumerate(raw_steps, start=1):
            input_payload = dict(item.get("input_payload", {}))
            for key, value in list(input_payload.items()):
                if isinstance(value, str):
                    input_payload[key] = value.replace("{objective}", objective)
            steps.append(
                ActionStep(
                    step_id=f"step-{index}",
                    capability_name=item["capability_name"],
                    description=item["description"],
                    input_payload=input_payload,
                )
            )
        return ExecutionPlan(skill_name=skill_name, objective=objective, steps=tuple(steps))
