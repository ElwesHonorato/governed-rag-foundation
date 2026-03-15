"""Sandbox policy checks."""

from __future__ import annotations

from pathlib import Path


class SandboxPolicy:
    """Workspace-bound path validation."""

    def __init__(self, workspace_root: str) -> None:
        self._workspace_root = Path(workspace_root).resolve()

    def validate_path(self, path: str) -> None:
        resolved = Path(path).resolve()
        try:
            resolved.relative_to(self._workspace_root)
        except ValueError as exc:
            raise ValueError(f"Path is outside the workspace: {path}") from exc
