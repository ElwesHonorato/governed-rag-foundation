"""Local filesystem gateway."""

from __future__ import annotations

from ai_infra.runtime.workspace_boundary import WorkspaceBoundary


class LocalFilesystemGateway:
    """Read-only workspace adapter."""

    def __init__(self, workspace_root: str) -> None:
        self._workspace = WorkspaceBoundary(workspace_root)

    def read_text(self, path: str) -> str:
        resolved = self._workspace.resolve_path(path)
        return resolved.read_text()
