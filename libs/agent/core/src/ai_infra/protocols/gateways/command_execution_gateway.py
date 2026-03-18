"""Command execution gateway interface."""

from __future__ import annotations

from typing import Protocol


class CommandExecutionGateway(Protocol):
    """Allowlisted command runner boundary."""

    def run(self, command: list[str]) -> dict[str, object]:
        """Execute an allowlisted command and return normalized output."""
