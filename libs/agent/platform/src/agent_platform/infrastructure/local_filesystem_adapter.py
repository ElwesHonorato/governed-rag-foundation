"""Local filesystem adapter."""

from __future__ import annotations

from pathlib import Path


class LocalFilesystemAdapter:
    """Read-only workspace adapter."""

    def __init__(self, workspace_root: str) -> None:
        self._workspace_root = Path(workspace_root).resolve()

    def read_text(self, path: str) -> str:
        resolved = (self._workspace_root / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
        resolved.relative_to(self._workspace_root)
        return resolved.read_text()
