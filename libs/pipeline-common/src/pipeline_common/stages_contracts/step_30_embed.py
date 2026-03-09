"""Step 30 embedding-stage contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from pipeline_common.stages_contracts.step_00_common import RegistryRowContract


class EmbeddingRegistryStatus(StrEnum):
    """Status values for embedding registry rows."""

    STARTED = "STARTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class EmbeddingProvenanceEnvelope:
    """Canonical embedding provenance envelope contract."""

    embedding_id: str
    chunk_id: str
    index_target: str
    embedder_name: str
    embedder_version: str
    embedding_params_hash: str
    embedding_dim: int
    embedding_vector_hash: str | None
    embedding_run_id: str
    run_id: str
    vector_record_id: str | None

    def to_dict(self) -> dict[str, Any]:
        """Serialize envelope for artifact persistence."""
        return asdict(self)


@dataclass(frozen=True)
class EmbeddingRegistryRow(EmbeddingProvenanceEnvelope, RegistryRowContract):
    """Authoritative embedding registry row contract."""

    attempt: int
    status: EmbeddingRegistryStatus
    error_message: str | None
    started_at: str
    finished_at: str | None
    upserted_at: str

    @classmethod
    def from_envelope(
        cls,
        *,
        envelope: EmbeddingProvenanceEnvelope,
        attempt: int,
        status: EmbeddingRegistryStatus,
        error_message: str | None,
        started_at: str,
        finished_at: str | None,
        upserted_at: str,
    ) -> "EmbeddingRegistryRow":
        """Build a registry row from a canonical embedding provenance envelope."""
        return cls(
            **envelope.to_dict(),
            attempt=attempt,
            status=status,
            error_message=error_message,
            started_at=started_at,
            finished_at=finished_at,
            upserted_at=upserted_at,
        )
