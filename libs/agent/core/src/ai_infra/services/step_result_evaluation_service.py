"""Step-result evaluation."""

from __future__ import annotations

from ai_infra.contracts.capability_result import CapabilityResult


class StepResultEvaluationService:
    """Simple success/failure evaluation for MVP steps."""

    def is_successful(self, result: CapabilityResult) -> bool:
        return result.success
