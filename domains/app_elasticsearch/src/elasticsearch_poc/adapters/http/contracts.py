"""HTTP contracts for the Elasticsearch retrieval API."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrieveRequest:
    """Typed request payload for the retrieval endpoint."""

    query: str
    limit: int

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "RetrieveRequest":
        """Build one retrieval request from dictionary payload data."""
        return cls(**payload)
