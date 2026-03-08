"""Typed output contract for chunk-text processor results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from contracts.chunk_manifest import ChunkManifestEntry


@dataclass(frozen=True)
class ChunkProcessOutput:
    chunk_count_expected: int
    chunk_count_written: int
    chunk_entries: list[ChunkManifestEntry]
    chunking_params: dict[str, Any]
