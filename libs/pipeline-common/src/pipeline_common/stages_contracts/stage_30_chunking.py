"""Stage 30 chunking contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, Mapping

from pipeline_common.stages_contracts.base import RegistryRowContract, SourceDocumentMetadata


class ChunkRegistryStatus(StrEnum):
    """Status values for chunk registry rows."""

    ACTIVE = "ACTIVE"
    DELETED = "DELETED"
    SUPERSEDED = "SUPERSEDED"


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
    chunker_version: str
    chunk_params_hash: str
    run_id: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize envelope for artifact persistence."""
        return asdict(self)


@dataclass(frozen=True)
class ChunkArtifactPayload:
    """Canonical chunk artifact payload persisted by stage-30 worker."""

    source_metadata: SourceDocumentMetadata
    provenance: ChunkProvenanceEnvelope
    chunk_index: int
    chunk_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_metadata": self.source_metadata.to_dict(),
            "provenance": self.provenance.to_dict(),
            "chunk_index": self.chunk_index,
            "chunk_text": self.chunk_text,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ChunkArtifactPayload":
        source_metadata_payload = data["source_metadata"]
        provenance_payload = data["provenance"]
        return cls(
            source_metadata=SourceDocumentMetadata(**dict(source_metadata_payload)),
            provenance=ChunkProvenanceEnvelope(**dict(provenance_payload)),
            chunk_index=int(data["chunk_index"]),
            chunk_text=str(data["chunk_text"]),
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
