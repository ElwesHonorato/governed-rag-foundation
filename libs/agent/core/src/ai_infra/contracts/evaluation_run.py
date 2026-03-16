"""Evaluation-run contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class EvaluationRun:
    """Offline evaluation result for a captured run."""

    run_id: str
    success: bool
    checks: dict[str, bool] = field(default_factory=dict)
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["notes"] = list(self.notes)
        return payload
