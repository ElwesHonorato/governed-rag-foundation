"""Termination policy checks."""

from __future__ import annotations

from ai_infra.contracts.agent_run import AgentRun


class TerminationPolicy:
    """Simple step-budget policy for the MVP."""

    def __init__(self, max_steps: int = 8) -> None:
        self._max_steps = max_steps

    def validate(self, run: AgentRun) -> None:
        if len(run.step_results) > self._max_steps:
            raise ValueError("Run exceeded configured step budget.")
