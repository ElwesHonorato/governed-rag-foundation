"""LLM gateway interface."""

from __future__ import annotations

from typing import Protocol


class LLMGateway(Protocol):
    """App-facing LLM boundary."""

    def generate(self, prompt: str, model: str) -> str:
        """Return generated text for the given prompt and model."""

    def chat(self, *, messages: list[dict[str, str]], model: str) -> str:
        """Return a chat-completion response for the given model."""
