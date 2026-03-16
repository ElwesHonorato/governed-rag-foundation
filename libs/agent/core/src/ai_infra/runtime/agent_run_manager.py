"""Run-manager contracts."""

from __future__ import annotations

from typing import Protocol

from ai_infra.contracts.agent_run import AgentRun


class AgentRunManager(Protocol):
    """Persistence boundary for runs."""

    def save_run(self, run: AgentRun) -> None:
        """Persist a run snapshot."""

    def load_run(self, run_id: str) -> AgentRun:
        """Load a previously saved run."""
