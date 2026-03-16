"""Local prompt repository."""

from __future__ import annotations

import json
from importlib.resources import files

from ai_infra.contracts.prompt_template import PromptTemplate


class LocalPromptRepository:
    """Loads prompt assets from packaged JSON resources."""

    def get_prompt(self, prompt_key: str) -> PromptTemplate:
        payload = json.loads(
            files("agent_platform.config").joinpath("prompts", f"{prompt_key}.json").read_text()
        )
        return PromptTemplate(
            prompt_key=payload["prompt_key"],
            version=payload["version"],
            system_instructions=payload["system_instructions"],
            user_template=payload["user_template"],
        )
