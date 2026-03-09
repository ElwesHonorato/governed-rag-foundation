"""Step 00 shared stage contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, ClassVar

PROCESSED_DOCUMENT_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class SourceDocumentMetadata:
    """Metadata contract for processed-document payloads."""

    FIELD_SCHEMA_VERSION: ClassVar[str] = "schema_version"
    FIELD_DOC_ID: ClassVar[str] = "doc_id"
    FIELD_SOURCE_KEY: ClassVar[str] = "source_key"
    FIELD_TIMESTAMP: ClassVar[str] = "timestamp"
    FIELD_SECURITY_CLEARANCE: ClassVar[str] = "security_clearance"
    FIELD_SOURCE_TYPE: ClassVar[str] = "source_type"
    FIELD_CONTENT_TYPE: ClassVar[str] = "content_type"
    FIELD_SOURCE_CONTENT_HASH: ClassVar[str] = "source_content_hash"

    schema_version: str
    doc_id: str
    source_key: str
    timestamp: str
    security_clearance: str
    source_type: str
    content_type: str
    source_content_hash: str

    @classmethod
    def build(
        cls,
        *,
        doc_id: str,
        source_key: str,
        timestamp: str,
        security_clearance: str,
        source_type: str,
        content_type: str,
        source_content_hash: str,
    ) -> "SourceDocumentMetadata":
        """Build versioned processed-document metadata."""
        return cls(
            schema_version=PROCESSED_DOCUMENT_SCHEMA_VERSION,
            doc_id=str(doc_id),
            source_key=str(source_key),
            timestamp=str(timestamp),
            security_clearance=str(security_clearance),
            source_type=str(source_type),
            content_type=str(content_type),
            source_content_hash=str(source_content_hash),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata to flat key/value payload fields."""
        return {
            self.FIELD_SCHEMA_VERSION: self.schema_version,
            self.FIELD_DOC_ID: self.doc_id,
            self.FIELD_SOURCE_KEY: self.source_key,
            self.FIELD_TIMESTAMP: self.timestamp,
            self.FIELD_SECURITY_CLEARANCE: self.security_clearance,
            self.FIELD_SOURCE_TYPE: self.source_type,
            self.FIELD_CONTENT_TYPE: self.content_type,
            self.FIELD_SOURCE_CONTENT_HASH: self.source_content_hash,
        }


@dataclass(frozen=True)
class ProcessorMetadata:
    """Common processor metadata contract shared across pipeline stages."""

    name: str
    version: str
    stage_name: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RegistryRowContract:
    """Shared behavior for provenance registry row contracts."""

    status: StrEnum

    def dump(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload
