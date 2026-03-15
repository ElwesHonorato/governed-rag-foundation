"""Model gateway interface."""

from __future__ import annotations

from typing import Protocol


class ModelGateway(Protocol):
    """Synthesis model boundary."""

    def synthesize(self, prompt: str, context: dict[str, object]) -> str:
        """Return final synthesized output."""
