"""Execution-journal helpers."""

from __future__ import annotations

from ai_infra.contracts.capability_result import CapabilityResult


class ExecutionJournal:
    """Formats execution results for persistence."""

    def to_record(self, result: CapabilityResult) -> dict[str, object]:
        return result.to_dict()
