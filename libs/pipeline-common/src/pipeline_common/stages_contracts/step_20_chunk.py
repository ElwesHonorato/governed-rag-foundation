"""Step 20 chunk-stage contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from pipeline_common.stages_contracts.step_00_common import RegistryRowContract


class ChunkRegistryStatus(StrEnum):
    """Status values for chunk registry rows."""

    ACTIVE = "ACTIVE"
    DELETED = "DELETED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True)
class ChunkRegistryRow(RegistryRowContract):
    """Authoritative chunking registry row contract."""

    chunk_id: str
    source_dataset_urn: str
    source_s3_uri: str
    source_content_hash: str
    chunk_s3_uri: str
    offsets_start: int
    offsets_end: int
    breadcrumb: str | None
    chunk_text_hash: str
    chunker_version: str
    chunk_params_hash: str
    run_id: str
    created_at: str
    observed_at: str
    status: ChunkRegistryStatus

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
