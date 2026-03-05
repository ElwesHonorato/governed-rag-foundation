"""Typed contracts for chunking and embedding provenance registries."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class ChunkRegistryStatus(StrEnum):
    """Status values for chunk registry rows."""

    ACTIVE = "ACTIVE"
    DELETED = "DELETED"
    SUPERSEDED = "SUPERSEDED"


class EmbeddingRegistryStatus(StrEnum):
    """Status values for embedding registry rows."""

    STARTED = "STARTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ChunkRegistryRow:
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
    chunker_name: str
    chunker_version: str
    chunk_params_hash: str
    chunking_run_id: str
    created_at: str
    observed_at: str
    status: ChunkRegistryStatus

    def dump(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


@dataclass(frozen=True)
class EmbeddingRegistryRow:
    """Authoritative embedding registry row contract."""

    embedding_id: str
    chunk_id: str
    index_target: str
    embedder_name: str
    embedder_version: str
    embedding_params_hash: str
    embedding_dim: int
    embedding_vector_hash: str | None
    embedding_run_id: str
    chunking_run_id: str
    attempt: int
    status: EmbeddingRegistryStatus
    error_message: str | None
    started_at: str
    finished_at: str | None
    upserted_at: str
    vector_record_id: str | None

    def dump(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload
