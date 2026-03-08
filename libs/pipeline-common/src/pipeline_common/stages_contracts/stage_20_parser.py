"""Stage 10 parser contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from pipeline_common.stages_contracts.base import SourceDocumentMetadata


@dataclass(frozen=True)
class ProcessorMetadata:
    """Parser runtime metadata attached to processed-document payloads."""

    name: str
    version: str

    @classmethod
    def build(
        cls,
        *,
        name: str,
        version: str,
    ) -> "ProcessorMetadata":
        return cls(
            name=str(name),
            version=str(version),
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ProcessorMetadata":
        raw_processor_metadata = payload["processor_metadata"]
        return cls.build(
            name=str(raw_processor_metadata["name"]),
            version=str(raw_processor_metadata["version"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ParsedTextPayload:
    """Canonical parsed text payload exchanged parse -> chunk workers."""

    title: str
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProcessedDocumentPayload:
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
    ) -> "ProcessedDocumentPayload":
        """Build a versioned processed-document payload."""
        return cls(
            metadata=metadata,
            processor_metadata=processor_metadata,
            parsed=parsed,
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ProcessedDocumentPayload":
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
