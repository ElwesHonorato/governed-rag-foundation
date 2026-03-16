"""Deterministic retrieval embedding used across local ingestion and query flows."""

from __future__ import annotations

import hashlib


class DeterministicRetrievalEmbedder:
    """Produce deterministic fixed-size vectors for retrieval pipelines."""

    def __init__(self, dimensions: int) -> None:
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        for index in range(self._dimensions):
            byte = digest[index % len(digest)]
            values.append((byte / 255.0) * 2.0 - 1.0)
        return values

    def similarity(self, left: list[float], right: list[float]) -> float:
        return sum(a * b for a, b in zip(left, right, strict=True))
