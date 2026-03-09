"""Stage 10 parser contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from pipeline_common.stages_contracts.base import ProcessorMetadata, SourceDocumentMetadata


@dataclass(frozen=True)
class ParsedTextPayload:
    """Canonical parsed text payload exchanged parse -> chunk workers."""

    title: str
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ParsedArtifactPayload:
    """Full processed-document payload contract exchanged parse -> chunk workers."""

    metadata: SourceDocumentMetadata
    processor_metadata: ProcessorMetadata
    parsed: ParsedTextPayload

    @classmethod
    def build(
        cls,
        *,
        metadata: SourceDocumentMetadata,
        processor_metadata: ProcessorMetadata,
        parsed: ParsedTextPayload,
    ) -> "ParsedArtifactPayload":
        """Build a versioned processed-document payload."""
        return cls(
            metadata=metadata,
            processor_metadata=processor_metadata,
            parsed=parsed,
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ParsedArtifactPayload":
        """Parse payload dict into typed processed-document contract."""
        metadata_payload = payload["metadata"]
        processor_metadata_payload = payload["processor_metadata"]
        parsed_payload = payload["parsed"]
        return cls(
            metadata=SourceDocumentMetadata(**dict(metadata_payload)),
            processor_metadata=ProcessorMetadata(**dict(processor_metadata_payload)),
            parsed=ParsedTextPayload(**dict(parsed_payload)),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize payload for object storage persistence."""
        return {
            "metadata": self.metadata.to_dict(),
            "processor_metadata": self.processor_metadata.to_dict(),
            "parsed": self.parsed.to_dict(),
        }
