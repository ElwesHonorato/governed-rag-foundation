"""Stage 10 parser contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Generic, Mapping, TypeVar

from pipeline_common.stages_contracts.step_00_common import ProcessorMetadata, SourceDocumentMetadata


@dataclass(frozen=True)
class ParsedTextPayload:
    """Canonical parsed text payload exchanged parse -> chunk workers."""

    title: str
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ContentT = TypeVar("ContentT")


@dataclass(frozen=True)
class ArtifactPayload(Generic[ContentT]):
    """Shared base payload for cross-worker artifact contracts."""

    source_metadata: SourceDocumentMetadata
    content: ContentT
    processor_metadata: ProcessorMetadata

    @classmethod
    def build(
        cls,
        *,
        source_metadata: SourceDocumentMetadata,
        processor_metadata: ProcessorMetadata,
        content: ContentT,
    ) -> "ArtifactPayload[ContentT]":
        """Build a versioned processed-document payload."""
        return cls(
            source_metadata=source_metadata,
            content=content,
            processor_metadata=processor_metadata,
        )

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
        *,
        content_type: type[ContentT],
    ) -> "ArtifactPayload[ContentT]":
        """Parse payload dict into typed processed-document contract."""
        source_metadata_payload = payload["source_metadata"]
        processor_metadata_payload = payload["processor_metadata"]
        content_payload = payload["content"]
        return cls(
            source_metadata=SourceDocumentMetadata(**dict(source_metadata_payload)),
            content=content_type(**dict(content_payload)),
            processor_metadata=ProcessorMetadata(**dict(processor_metadata_payload)),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize payload for object storage persistence."""
        return asdict(self)


@dataclass(frozen=True)
class ChunkArtifactPayload(ArtifactPayload[ParsedTextPayload]):
    """Typed chunk artifact payload contract."""
