"""Vector search gateway interface."""

from __future__ import annotations

from typing import Protocol


class VectorSearchGateway(Protocol):
    """Vector retrieval boundary."""

    def search(self, query: str, top_k: int) -> list[dict[str, object]]:
        """Return ranked retrieval hits."""
