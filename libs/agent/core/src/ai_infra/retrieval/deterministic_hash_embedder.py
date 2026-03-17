"""Deterministic hash embedding used across local ingestion and query flows."""

from __future__ import annotations

import hashlib
import math


class DeterministicHashEmbedder:
    """Produce deterministic fixed-size hash-based vectors for testing."""

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
        if len(left) != len(right):
            raise ValueError("Vectors must have the same length")

        dot = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))

        if left_norm == 0.0 or right_norm == 0.0:
            raise ValueError("Cannot compute cosine similarity for zero vectors")

        return dot / (left_norm * right_norm)
