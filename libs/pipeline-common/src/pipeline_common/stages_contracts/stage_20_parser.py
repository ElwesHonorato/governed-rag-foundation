"""Stage 10 parser contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from pipeline_common.stages_contracts.base import SourceDocumentMetadata


@dataclass(frozen=True)
class ProcessorMetadata:
    """Parser runtime metadata attached to processed-document payloads."""

    parser_version: str

    @classmethod
    def build(
        cls,
        *,
        parser_version: str,
    ) -> "ProcessorMetadata":
        return cls(
            parser_version=str(parser_version),
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ProcessorMetadata":
        raw_processor_metadata = payload["processor_metadata"]
        return cls.build(
            parser_version=str(raw_processor_metadata["parser_version"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "parser_version": self.parser_version,
        }


@dataclass(frozen=True)
class ProcessedDocumentPayload:
    """Full processed-document payload contract exchanged parse -> chunk workers."""

    metadata: SourceDocumentMetadata
    processor_metadata: ProcessorMetadata
    parsed: dict[str, Any]

    @classmethod
    def build(
        cls,
        *,
        metadata: SourceDocumentMetadata,
        processor_metadata: ProcessorMetadata,
        parsed: Mapping[str, Any],
    ) -> "ProcessedDocumentPayload":
        """Build a versioned processed-document payload."""
        return cls(
            metadata=metadata,
            processor_metadata=processor_metadata,
            parsed=dict(parsed),
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ProcessedDocumentPayload":
        """Parse payload dict into typed processed-document contract."""
        return cls(
            metadata=SourceDocumentMetadata.from_payload(payload),
            processor_metadata=ProcessorMetadata.from_payload(payload),
            parsed=dict(payload["parsed"]),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize payload for object storage persistence."""
        return {
            **self.metadata.to_dict(),
            "processor_metadata": self.processor_metadata.to_dict(),
            "parsed": dict(self.parsed),
        }
