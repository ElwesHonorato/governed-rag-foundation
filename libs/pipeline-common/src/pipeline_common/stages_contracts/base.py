"""Base contracts shared across stage payload contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, ClassVar, Mapping

PROCESSED_DOCUMENT_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class SourceDocumentMetadata:
    """Metadata contract for processed-document payloads."""

    FIELD_SCHEMA_VERSION: ClassVar[str] = "schema_version"
    FIELD_DOC_ID: ClassVar[str] = "doc_id"
    FIELD_SOURCE_KEY: ClassVar[str] = "source_key"
    FIELD_TIMESTAMP: ClassVar[str] = "timestamp"
    FIELD_SECURITY_CLEARANCE: ClassVar[str] = "security_clearance"

    schema_version: str
    doc_id: str
    source_key: str
    timestamp: str
    security_clearance: str

    @classmethod
    def build(
        cls,
        *,
        doc_id: str,
        source_key: str,
        timestamp: str,
        security_clearance: str,
    ) -> "SourceDocumentMetadata":
        """Build versioned processed-document metadata."""
        return cls(
            schema_version=PROCESSED_DOCUMENT_SCHEMA_VERSION,
            doc_id=str(doc_id),
            source_key=str(source_key),
            timestamp=str(timestamp),
            security_clearance=str(security_clearance),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata to flat key/value payload fields."""
        return {
            self.FIELD_SCHEMA_VERSION: self.schema_version,
            self.FIELD_DOC_ID: self.doc_id,
            self.FIELD_SOURCE_KEY: self.source_key,
            self.FIELD_TIMESTAMP: self.timestamp,
            self.FIELD_SECURITY_CLEARANCE: self.security_clearance,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "SourceDocumentMetadata":
        """Parse metadata fields from a flat processed-document payload."""
        return cls(
            **{
                "schema_version": str(payload[cls.FIELD_SCHEMA_VERSION]),
                "doc_id": str(payload[cls.FIELD_DOC_ID]),
                "source_key": str(payload[cls.FIELD_SOURCE_KEY]),
                "timestamp": str(payload[cls.FIELD_TIMESTAMP]),
                "security_clearance": str(payload[cls.FIELD_SECURITY_CLEARANCE]),
            }
        )


class RegistryRowContract:
    """Shared behavior for provenance registry row contracts."""

    status: StrEnum

    def dump(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload
