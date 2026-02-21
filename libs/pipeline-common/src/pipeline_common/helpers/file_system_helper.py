"""Process-agnostic filesystem helper utilities."""

from __future__ import annotations

from pathlib import Path


class FileSystemHelper:
    """Provide process-agnostic filesystem helpers."""

    @classmethod
    def find_dir_upwards(cls, path: Path, n: int) -> Path:
        """Return the `n`-th parent directory from `path`."""

        if n < 0:
            raise ValueError("n must be >= 0")
        return path.resolve().parents[n]
