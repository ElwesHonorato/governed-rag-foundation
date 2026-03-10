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

    @property
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ContentT = TypeVar("ContentT")


@dataclass(frozen=True)
class StageArtifact(Generic[ContentT]):
    """Shared base payload for cross-worker artifact contracts."""

    source_metadata: SourceDocumentMetadata
    content: ContentT
    processor_metadata: ProcessorMetadata

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
        *,
        content_type: type[ContentT],
    ) -> "StageArtifact[ContentT]":
        """Parse payload dict into typed processed-document contract."""
        return cls(
            source_metadata=SourceDocumentMetadata(**payload["source_metadata"]),
            content=content_type(**payload["content"]),
            processor_metadata=ProcessorMetadata(**payload["processor_metadata"]),
        )

    @property
    def to_dict(self) -> dict[str, Any]:
        """Serialize payload for object storage persistence."""
        return asdict(self)
