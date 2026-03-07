"""Stage 30 chunking contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, Mapping

from pipeline_common.stages_contracts.base import RegistryRowContract


class ChunkRegistryStatus(StrEnum):
    """Status values for chunk registry rows."""

    ACTIVE = "ACTIVE"
    DELETED = "DELETED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True)
class ChunkDocumentMetadata:
    """Stage-30 metadata carried with LangChain split documents."""

    doc_id: str
    timestamp: str
    security_clearance: str
    source_dataset_urn: str
    source_s3_uri: str
    source_content_hash: str
    chunking_run_id: str
    source_type: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain metadata dict expected by splitters/documents."""
        return asdict(self)


@dataclass(frozen=True)
class ChunkProvenanceEnvelope:
    """Canonical chunk provenance envelope contract."""

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

    def to_dict(self) -> dict[str, Any]:
        """Serialize envelope for artifact persistence."""
        return asdict(self)


@dataclass(frozen=True)
class ChunkArtifactPayload:
    """Canonical chunk artifact payload persisted by stage-30 worker."""

    doc_id: str
    chunk_id: str
    chunk_index: int
    chunk_text: str
    source_type: str
    timestamp: str
    security_clearance: str | None
    source_dataset_urn: str
    source_s3_uri: str
    source_content_hash: str
    offsets_start: int
    offsets_end: int
    breadcrumb: str
    chunking_run_id: str
    chunk_text_hash: str
    chunker_name: str
    chunker_version: str
    chunk_params_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ChunkArtifactPayload":
        return cls(
            doc_id=str(data["doc_id"]),
            chunk_id=str(data["chunk_id"]),
            chunk_index=int(data["chunk_index"]),
            chunk_text=str(data["chunk_text"]),
            source_type=str(data["source_type"]),
            timestamp=str(data["timestamp"]),
            security_clearance=str(data["security_clearance"]) if data.get("security_clearance") is not None else None,
            source_dataset_urn=str(data["source_dataset_urn"]),
            source_s3_uri=str(data["source_s3_uri"]),
            source_content_hash=str(data["source_content_hash"]),
            offsets_start=int(data["offsets_start"]),
            offsets_end=int(data["offsets_end"]),
            breadcrumb=str(data["breadcrumb"]),
            chunking_run_id=str(data["chunking_run_id"]),
            chunk_text_hash=str(data["chunk_text_hash"]),
            chunker_name=str(data["chunker_name"]),
            chunker_version=str(data["chunker_version"]),
            chunk_params_hash=str(data["chunk_params_hash"]),
        )


@dataclass(frozen=True)
class ChunkRegistryRow(ChunkProvenanceEnvelope, RegistryRowContract):
    """Authoritative chunking registry row contract."""

    created_at: str
    observed_at: str
    status: ChunkRegistryStatus

    @classmethod
    def from_envelope(
        cls,
        *,
        envelope: ChunkProvenanceEnvelope,
        created_at: str,
        observed_at: str,
        status: ChunkRegistryStatus,
    ) -> "ChunkRegistryRow":
        """Build a registry row from a canonical chunk provenance envelope."""
        return cls(
            **envelope.to_dict(),
            created_at=created_at,
            observed_at=observed_at,
            status=status,
        )
