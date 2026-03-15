"""Allowlisted command runner."""

from __future__ import annotations

import subprocess
from pathlib import Path


class LocalCommandRunner:
    """Runs a minimal allowlisted command set without a shell."""

    def __init__(self, workspace_root: str) -> None:
        self._workspace_root = Path(workspace_root)

    def run(self, command: list[str]) -> dict[str, object]:
        self._validate(command)
        completed = subprocess.run(
            command,
            cwd=self._workspace_root,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }

    def _validate(self, command: list[str]) -> None:
        if not command:
            raise ValueError("Command cannot be empty.")
        head = command[0]
        if head == "git":
            if command[1:] not in (["status"], ["status", "--short"]):
                raise ValueError("Only `git status` is allowed in MVP.")
            return
        if head == "ls":
            return
        if head == "rg":
            return
        raise ValueError(f"Command is not allowlisted: {head}")
