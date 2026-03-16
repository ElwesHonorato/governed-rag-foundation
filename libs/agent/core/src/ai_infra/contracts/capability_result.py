"""Capability result contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class CapabilityResult:
    """Normalized capability execution result."""

    capability_name: str
    step_id: str
    success: bool
    output: dict[str, object] = field(default_factory=dict)
    error_message: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
