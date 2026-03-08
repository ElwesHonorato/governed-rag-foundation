"""Stage 10 parser contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Mapping

from pipeline_common.stages_contracts.base import SourceDocumentMetadata


@dataclass(frozen=True)
class ProcessedDocumentPayload:
    """Full processed-document payload contract exchanged parse -> chunk workers."""

    FIELD_PARSED: ClassVar[str] = "parsed"

    metadata: SourceDocumentMetadata
    parsed: dict[str, Any]

    @classmethod
    def build(
        cls,
        *,
        doc_id: str,
        source_key: str,
        timestamp: str,
        security_clearance: str,
        source_type: str | None = None,
        parsed: Mapping[str, Any],
    ) -> "ProcessedDocumentPayload":
        """Build a versioned processed-document payload."""
        resolved_source_type = source_type
        if resolved_source_type is None:
            resolved_source_type = Path(source_key).suffix.lower().lstrip(".")
        return cls(
            metadata=SourceDocumentMetadata.build(
                doc_id=doc_id,
                source_key=source_key,
                timestamp=timestamp,
                security_clearance=security_clearance,
                source_type=resolved_source_type,
            ),
            parsed=dict(parsed),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize payload for object storage persistence."""
        return {
            **self.metadata.to_dict(),
            self.FIELD_PARSED: dict(self.parsed),
        }
