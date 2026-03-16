"""Capability request contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class CapabilityRequest:
    """Normalized request sent to a capability executor."""

    capability_name: str
    session_id: str
    run_id: str
    step_id: str
    input_payload: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
