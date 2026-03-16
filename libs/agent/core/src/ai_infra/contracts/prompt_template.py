"""Prompt-template contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PromptTemplate:
    """Versioned prompt asset."""

    prompt_key: str
    version: str
    system_instructions: str
    user_template: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
