"""Stage 10 parser contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from pipeline_common.stages_contracts.base import SourceDocumentMetadata


@dataclass(frozen=True)
class ProcessedDocumentPayload:
    """Full processed-document payload contract exchanged parse -> chunk workers."""

    metadata: SourceDocumentMetadata
    parsed: dict[str, Any]

    @classmethod
    def build(
        cls,
        *,
        metadata: SourceDocumentMetadata,
        parsed: Mapping[str, Any],
    ) -> "ProcessedDocumentPayload":
        """Build a versioned processed-document payload."""
        return cls(
            metadata=metadata,
            parsed=dict(parsed),
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ProcessedDocumentPayload":
        """Parse payload dict into typed processed-document contract."""
        return cls(
            metadata=SourceDocumentMetadata.from_payload(payload),
            parsed=dict(payload["parsed"]),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize payload for object storage persistence."""
        return {
            **self.metadata.to_dict(),
            "parsed": dict(self.parsed),
        }
