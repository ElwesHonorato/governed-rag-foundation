"""Replan decision contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ReplanDecision:
    """Signals whether a failed run can continue with a revised plan."""

    should_replan: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
