"""Allowlisted command gateway."""

from __future__ import annotations

import subprocess
from pathlib import Path


class LocalCommandGateway:
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
            for argument in command[1:]:
                if argument.startswith("-"):
                    continue
                self._validate_path_argument(argument)
            return
        if head == "rg":
            self._validate_rg_arguments(command[1:])
            return
        raise ValueError(f"Command is not allowlisted: {head}")

    def _validate_rg_arguments(self, arguments: list[str]) -> None:
        pattern_seen = False
        for argument in arguments:
            if not pattern_seen:
                if argument.startswith("-"):
                    continue
                pattern_seen = True
                continue
            if argument.startswith("-"):
                raise ValueError("rg options after the search pattern are not supported.")
            self._validate_path_argument(argument)

    def _validate_path_argument(self, argument: str) -> None:
        resolved = (self._workspace_root / argument).resolve()
        try:
            resolved.relative_to(self._workspace_root.resolve())
        except ValueError as exc:
            raise ValueError(f"Command path is outside the workspace: {argument}") from exc
