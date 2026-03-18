"""Execution-step contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class ActionStep:
    """Single supervised capability invocation."""

    step_id: str
    capability_name: str
    description: str
    input_payload: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
