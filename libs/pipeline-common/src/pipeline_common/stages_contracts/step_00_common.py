"""Step 00 shared stage contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, ClassVar


@dataclass(frozen=True)
class RootDocumentMetadata:
    """Metadata contract for root-document payloads."""

    SCHEMA_VERSION: ClassVar[str] = "1.0"
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
    ) -> "RootDocumentMetadata":
        """Build versioned root-document metadata."""
        return cls(
            schema_version=cls.SCHEMA_VERSION,
            doc_id=str(doc_id),
            source_key=str(source_key),
            timestamp=str(timestamp),
            security_clearance=str(security_clearance),
            source_type=str(source_type),
            content_type=str(content_type),
            source_content_hash=str(source_content_hash),
        )

    @property
    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata to flat key/value payload fields."""
        return asdict(self)


@dataclass(frozen=True)
class ProcessorMetadata:
    """Common processor metadata contract shared across pipeline stages."""

    name: str
    version: str

    @property
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
