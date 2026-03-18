"""Sandbox policy checks."""

from __future__ import annotations

from ai_infra.runtime.workspace_boundary import WorkspaceBoundary


class SandboxPolicy:
    """Workspace-bound path validation."""

    def __init__(self, workspace_root: str) -> None:
        self._workspace = WorkspaceBoundary(workspace_root)

    def validate_path(self, path: str) -> None:
        self._workspace.ensure_within(path)

    def validate_command(self, command: list[str]) -> None:
        if not command:
            raise ValueError("Command cannot be empty.")
        head = command[0]
        if head == "git":
            return
        if head == "ls":
            for argument in command[1:]:
                if argument.startswith("-"):
                    continue
                self._validate_relative_argument(argument)
            return
        if head == "rg":
            self._validate_rg_arguments(command[1:])
            return
        raise ValueError(f"Command is not sandbox-approved: {head}")

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
            self._validate_relative_argument(argument)

    def _validate_relative_argument(self, argument: str) -> None:
        self._workspace.resolve_path(argument)
