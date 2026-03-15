"""Prompt repository interface."""

from __future__ import annotations

from typing import Protocol

from ai_infra.contracts.prompt_template import PromptTemplate


class PromptTemplateRepository(Protocol):
    """Prompt asset boundary."""

    def get_prompt(self, prompt_key: str) -> PromptTemplate:
        """Return the configured prompt template."""
