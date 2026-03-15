"""Session manager."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from ai_infra.contracts.agent_session import AgentSession
from ai_infra.contracts.session_state import SessionState
from ai_infra.kernel.session_state_store import SessionStateStore


class AgentSessionManager:
    """Creates and updates sessions."""

    def __init__(self, session_store: SessionStateStore) -> None:
        self._session_store = session_store

    def create_session(self, objective: str, skill_name: str) -> AgentSession:
        timestamp = datetime.now(UTC).isoformat()
        session = AgentSession(
            session_id=f"session-{uuid4().hex[:12]}",
            objective=objective,
            skill_name=skill_name,
            state=SessionState(status="created"),
            created_at=timestamp,
            updated_at=timestamp,
        )
        self._session_store.save_session(session)
        return session

    def attach_run(self, session: AgentSession, run_id: str) -> AgentSession:
        updated = replace(
            session,
            state=SessionState(status="running", current_run_id=run_id),
            updated_at=datetime.now(UTC).isoformat(),
            run_ids=tuple(list(session.run_ids) + [run_id]),
        )
        self._session_store.save_session(updated)
        return updated

    def update_run_status(self, session: AgentSession, run_id: str, status: str) -> AgentSession:
        updated = replace(
            session,
            state=SessionState(status=status, current_run_id=run_id),
            updated_at=datetime.now(UTC).isoformat(),
        )
        self._session_store.save_session(updated)
        return updated
