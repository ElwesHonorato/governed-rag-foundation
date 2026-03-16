"""Session-state store boundary."""

from __future__ import annotations

from typing import Protocol

from ai_infra.contracts.agent_session import AgentSession


class SessionStateStore(Protocol):
    """Persistence boundary for sessions."""

    def save_session(self, session: AgentSession) -> None:
        """Persist a session."""

    def load_session(self, session_id: str) -> AgentSession:
        """Load a session."""
