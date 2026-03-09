"""Step 20 chunk-stage contracts."""

from __future__ import annotations

from enum import StrEnum


class ChunkRegistryStatus(StrEnum):
    """Status values for chunk registry rows."""

    ACTIVE = "ACTIVE"
    DELETED = "DELETED"
    SUPERSEDED = "SUPERSEDED"
