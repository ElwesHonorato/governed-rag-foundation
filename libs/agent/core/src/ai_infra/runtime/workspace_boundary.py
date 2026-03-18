"""Workspace-bound path resolution helpers."""

from __future__ import annotations

from pathlib import Path


class WorkspaceBoundary:
    """Resolve and validate paths against one workspace root."""

    def __init__(self, workspace_root: str) -> None:
        self._workspace_root = Path(workspace_root).resolve()

    @property
    def root(self) -> Path:
        return self._workspace_root

    def resolve_path(self, path: str) -> Path:
        candidate = Path(path)
        resolved = candidate.resolve() if candidate.is_absolute() else (self._workspace_root / candidate).resolve()
        self.ensure_within(resolved)
        return resolved

    def ensure_within(self, path: str | Path) -> Path:
        resolved = Path(path).resolve()
        try:
            resolved.relative_to(self._workspace_root)
        except ValueError as exc:
            raise ValueError(f"Path is outside the workspace: {path}") from exc
        return resolved
