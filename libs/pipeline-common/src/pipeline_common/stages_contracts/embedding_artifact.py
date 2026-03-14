"""Canonical embedding artifact contracts shared by embed and index workers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from pipeline_common.stages_contracts.step_00_common import FileMetadata


@dataclass(frozen=True)
class EmbeddingArtifactMetadata:
    """Metadata stored with one embedding artifact."""

    run_id: str
    embedder_name: str
    embedder_version: str
    embedding_params_hash: str
    embedding_run_id: str
    root_doc_metadata: FileMetadata
    stage_doc_metadata: FileMetadata

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EmbeddingArtifactMetadata":
        """Parse embedding artifact metadata from storage JSON."""
        metadata_payload = dict(payload)
        metadata_payload["root_doc_metadata"] = FileMetadata.from_dict(metadata_payload["root_doc_metadata"])
        metadata_payload["stage_doc_metadata"] = FileMetadata.from_dict(metadata_payload["stage_doc_metadata"])
        return cls(**metadata_payload)

    @property
    def to_dict(self) -> dict[str, Any]:
        """Serialize embedding artifact metadata for storage persistence."""
        return asdict(self)


@dataclass(frozen=True)
class EmbeddingArtifact:
    """Canonical persisted embedding artifact contract."""

    doc_id: str
    chunk_id: str
    chunk_text: str
    vector: list[float]
    metadata: EmbeddingArtifactMetadata

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EmbeddingArtifact":
        """Parse one embedding artifact from storage JSON."""
        return cls(
            doc_id=str(payload["doc_id"]),
            chunk_id=str(payload["chunk_id"]),
            chunk_text=str(payload["chunk_text"]),
            vector=[float(value) for value in payload["vector"]],
            metadata=EmbeddingArtifactMetadata.from_dict(dict(payload["metadata"])),
        )

    @property
    def to_dict(self) -> dict[str, Any]:
        """Serialize one embedding artifact for storage persistence."""
        return asdict(self)
