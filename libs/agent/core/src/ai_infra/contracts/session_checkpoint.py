"""Checkpoint contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class SessionCheckpoint:
    """Persisted run snapshot."""

    checkpoint_id: str
    run_id: str
    session_id: str
    snapshot: dict[str, object] = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
