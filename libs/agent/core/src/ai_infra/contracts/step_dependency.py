"""Step dependency contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class StepDependency:
    """Declares that one step depends on another step result."""

    step_id: str
    depends_on_step_id: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
