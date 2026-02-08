from __future__ import annotations

from rag_api.llm_client import OllamaClient


def normalize_prompt(raw_prompt: object) -> str:
    if not isinstance(raw_prompt, str):
        raise ValueError("prompt must be a string")

    prompt_text = raw_prompt.strip()
    if not prompt_text:
        raise ValueError("prompt is required")
    if len(prompt_text) > 2000:
        raise ValueError("prompt is too long (max 2000 characters)")

    return prompt_text


def run_prompt(*, prompt: str, model: str, llm_client: OllamaClient) -> dict[str, str]:
    response = llm_client.generate(prompt=prompt, model=model)
    return {
        "prompt": prompt,
        "model": model,
        "response": response,
    }
