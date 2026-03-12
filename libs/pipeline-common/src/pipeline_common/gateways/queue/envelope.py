from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, Mapping


class QueueMessageType(StrEnum):
    """Known queue message types exchanged between workers."""

    PARSE_DOCUMENT_REQUEST = "parse_document.request"
    CHUNK_TEXT_REQUEST = "chunk_text.request"
    EMBED_CHUNKS_REQUEST = "embed_chunks.request"
    INDEX_WEAVIATE_REQUEST = "index_weaviate.request"
    PARSE_DOCUMENT_FAILURE = "parse_document.failure"
    CHUNK_TEXT_FAILURE = "chunk_text.failure"
    EMBED_CHUNKS_FAILURE = "embed_chunks.failure"
    INDEX_WEAVIATE_FAILURE = "index_weaviate.failure"
    PARSE_DOCUMENT_INVALID_MESSAGE = "parse_document.invalid_message"
    EMBED_CHUNKS_INVALID_MESSAGE = "embed_chunks.invalid_message"
    INDEX_WEAVIATE_INVALID_MESSAGE = "index_weaviate.invalid_message"


@dataclass(frozen=True)
class Envelope:
    """Standard queue envelope for worker message transport."""

    type: str | QueueMessageType
    payload: dict[str, Any]
    meta: dict[str, Any] | None = None

    @property
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def to_payload(self) -> dict[str, Any]:
        out = {"type": self.type, "payload": self.payload}
        if self.meta:
            out["meta"] = self.meta
        return out

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Envelope":
        return cls(
            type=str(raw["type"]),
            payload=dict(raw["payload"]),
            meta=dict(raw["meta"]) if "meta" in raw else None,
        )
