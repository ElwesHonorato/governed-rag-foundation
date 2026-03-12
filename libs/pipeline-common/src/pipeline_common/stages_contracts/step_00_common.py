"""Step 00 shared stage contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar, Mapping


@dataclass(frozen=True)
class RootDocumentMetadata:
    """Metadata contract for root-document payloads.

    Attributes:
        doc_id: Stable identifier of the logical document.
        source_uri: Storage URI where the original file resides.
        timestamp: ISO timestamp representing ingestion or creation time.
        security_clearance: Security classification required to access the document.
        source_type: Origin of the document (e.g. email, pdf, contract).
        content_type: MIME type of the source document.
        source_content_hash: SHA256 hash of the original document content.
        schema_version: Version of the metadata schema.
    """

    SCHEMA_VERSION: ClassVar[str] = "1.0"

    doc_id: str
    source_uri: str
    timestamp: str
    security_clearance: str
    source_type: str
    content_type: str
    source_content_hash: str
    schema_version: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", self.SCHEMA_VERSION)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RootDocumentMetadata":
        """Build metadata from a payload while enforcing the current schema version."""
        metadata_payload = dict(payload)
        metadata_payload.pop("schema_version", None)
        return cls(**metadata_payload)

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
