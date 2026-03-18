"""Prompt-version contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PromptVersion:
    """Prompt version selected for a run."""

    prompt_key: str
    version: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
