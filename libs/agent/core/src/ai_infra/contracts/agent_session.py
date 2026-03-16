"""Session contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from ai_infra.contracts.session_state import SessionState


@dataclass(frozen=True)
class AgentSession:
    """Long-lived agent session."""

    session_id: str
    objective: str
    skill_name: str
    state: SessionState
    created_at: str
    updated_at: str
    run_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["state"] = self.state.to_dict()
        payload["run_ids"] = list(self.run_ids)
        return payload
