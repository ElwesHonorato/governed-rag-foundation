"""Elasticsearch queue and document contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ElasticsearchIndexWorkItem:
    """Queue contract for one Elasticsearch indexing request."""

    uri: str
    doc_id: str
    chunk_id: str
    stage: str = "chunk_text"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ElasticsearchIndexWorkItem":
        """Build a typed work item from queue payload data."""
        return cls(
            uri=str(payload["uri"]),
            doc_id=str(payload["doc_id"]),
            chunk_id=str(payload["chunk_id"]),
            stage=str(payload.get("stage", "chunk_text")),
        )

    @property
    def to_dict(self) -> dict[str, str]:
        """Serialize the queue work item."""
        return asdict(self)


@dataclass(frozen=True)
class IndexedChunkDocument:
    """Canonical Elasticsearch document built from one chunk ``StageArtifact``."""

    document_id: str
    chunk_id: str
    doc_id: str
    chunk_text: str
    source_uri: str
    artifact_uri: str
    content_type: str
    created_at: str
    security_clearance: str
    source_type: str
    chunk_text_hash: str
    offsets_start: int
    offsets_end: int
    processor_name: str
    processor_version: str
    metadata: dict[str, Any]

    @property
    def to_dict(self) -> dict[str, Any]:
        """Serialize the Elasticsearch document body."""
        payload = asdict(self)
        payload.pop("document_id")
        return payload


@dataclass(frozen=True)
class ElasticsearchRetrievedDocument:
    """Normalized retrieval hit returned from Elasticsearch queries."""

    chunk_id: str
    doc_id: str
    chunk_text: str
    source_uri: str
    artifact_uri: str
    security_clearance: str
    score: float

    @property
    def to_dict(self) -> dict[str, Any]:
        """Serialize the retrieval hit for HTTP responses."""
        return asdict(self)
