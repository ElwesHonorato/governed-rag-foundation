"""Filesystem gateway interface."""

from __future__ import annotations

from typing import Protocol


class FilesystemGateway(Protocol):
    """Read-only filesystem boundary."""

    def read_text(self, path: str) -> str:
        """Return file contents within the allowed workspace."""
