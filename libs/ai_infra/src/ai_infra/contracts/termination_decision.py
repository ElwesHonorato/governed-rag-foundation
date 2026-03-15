"""Termination decision contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TerminationDecision:
    """Terminal run outcome."""

    status: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
