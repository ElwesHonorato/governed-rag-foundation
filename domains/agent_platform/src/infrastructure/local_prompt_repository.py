"""Local prompt repository."""

from __future__ import annotations

import json
from pathlib import Path

from ai_infra.contracts.prompt_template import PromptTemplate


class LocalPromptRepository:
    """Loads prompt assets from local JSON files."""

    def __init__(self, prompts_dir: str) -> None:
        self._prompts_dir = Path(prompts_dir)

    def get_prompt(self, prompt_key: str) -> PromptTemplate:
        payload = json.loads((self._prompts_dir / f"{prompt_key}.json").read_text())
        return PromptTemplate(
            prompt_key=payload["prompt_key"],
            version=payload["version"],
            system_instructions=payload["system_instructions"],
            user_template=payload["user_template"],
        )
