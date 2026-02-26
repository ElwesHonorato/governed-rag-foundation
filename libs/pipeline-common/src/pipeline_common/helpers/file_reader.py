"""Extension-based file reader helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import yaml


class FileReader:
    """Read files from paths using extension-based readers."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.default_reader: Callable[[Path], dict[str, Any]] = self._read_yaml
        self.extension_readers: dict[str, Callable[[Path], dict[str, Any]]] = {
            ".yaml": self._read_yaml,
            ".yml": self._read_yaml,
        }

    def read(self) -> dict[str, Any]:
        extension = self.path.suffix.lower()
        reader = self.extension_readers.get(extension, self.default_reader)
        return reader(self.path)

    def _read_yaml(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as file_handle:
            data = yaml.safe_load(file_handle) or {}
        if not isinstance(data, dict):
            raise ValueError(f"Expected top-level mapping in {path}")
        return data
