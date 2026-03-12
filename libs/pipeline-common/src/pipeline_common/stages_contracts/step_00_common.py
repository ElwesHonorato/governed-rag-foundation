"""Step 00 shared stage contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar


@dataclass(frozen=True)
class RootDocumentMetadata:
    """Metadata contract for root-document payloads."""

    SCHEMA_VERSION: ClassVar[str] = "1.0"

    doc_id: str
    source_key: str
    timestamp: str
    security_clearance: str
    source_type: str
    content_type: str
    source_content_hash: str
    schema_version: str = field(default=SCHEMA_VERSION)

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
