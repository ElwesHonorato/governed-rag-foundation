"""Response validation."""

from __future__ import annotations

from ai_infra.contracts.capability_result import CapabilityResult


class ResponseValidationService:
    """Validates normalized synthesis output."""

    def validate(self, result: CapabilityResult) -> None:
        if result.capability_name != "llm_synthesize" or not result.success:
            return
        if not str(result.output.get("text", "")).strip():
            raise ValueError("llm_synthesize returned empty output.")
