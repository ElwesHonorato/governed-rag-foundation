"""Next-step decision contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class NextStepDecision:
    """Supervisor choice for the next step."""

    step_id: str | None
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
