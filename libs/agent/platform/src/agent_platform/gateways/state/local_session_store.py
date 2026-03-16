"""File-backed session store."""

from __future__ import annotations

import json
from pathlib import Path

from ai_infra.contracts.agent_session import AgentSession
from ai_infra.contracts.session_state import SessionState


class LocalSessionStore:
    """Persists sessions as JSON files."""

    def __init__(self, base_dir: str) -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def save_session(self, session: AgentSession) -> None:
        (self._base_dir / f"{session.session_id}.json").write_text(json.dumps(session.to_dict(), indent=2))

    def load_session(self, session_id: str) -> AgentSession:
        payload = json.loads((self._base_dir / f"{session_id}.json").read_text())
        return AgentSession(
            session_id=payload["session_id"],
            objective=payload["objective"],
            skill_name=payload["skill_name"],
            state=SessionState(
                status=payload["state"]["status"],
                current_run_id=payload["state"].get("current_run_id"),
            ),
            created_at=payload["created_at"],
            updated_at=payload["updated_at"],
            run_ids=tuple(payload.get("run_ids", [])),
        )
