"""Session-state contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SessionState:
    """High-level session state."""

    status: str
    current_run_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
