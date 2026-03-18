"""Grounded response contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Citation:
    """Citation returned with a grounded answer."""

    source_uri: str
    doc_id: str
    chunk_id: str
    quote: str
    distance: float | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GroundedResponse:
    """Grounded response returned from the agent runtime."""

    model: str
    response: str
    assistant_message: dict[str, str]
    citations: list[Citation]

    def to_dict(self) -> dict[str, object]:
        return {
            "model": self.model,
            "response": self.response,
            "assistant_message": dict(self.assistant_message),
            "citations": [citation.to_dict() for citation in self.citations],
        }
