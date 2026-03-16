"""Capability metadata contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class CapabilityDescriptor:
    """Policy-facing description of a capability."""

    name: str
    category: str
    backend_kind: str
    version: str
    risk_classification: str
    input_schema_ref: str
    output_schema_ref: str
    side_effect_flag: bool = False
    preconditions: tuple[str, ...] = field(default_factory=tuple)
    postconditions: tuple[str, ...] = field(default_factory=tuple)
    invariants: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["preconditions"] = list(self.preconditions)
        payload["postconditions"] = list(self.postconditions)
        payload["invariants"] = list(self.invariants)
        return payload
