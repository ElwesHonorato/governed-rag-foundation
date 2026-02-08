from __future__ import annotations

from rag_api.llm_client import OllamaClient


class PromptService:
    def __init__(self, *, llm_client: OllamaClient, model: str) -> None:
        self.llm_client = llm_client
        self.model = model

    def normalize_prompt(self, payload: dict[str, object]) -> str:
        raw_prompt = payload.get("prompt", "")
        if not isinstance(raw_prompt, str):
            raise ValueError("prompt must be a string")

        prompt_text = raw_prompt.strip()
        if not prompt_text:
            raise ValueError("prompt is required")
        if len(prompt_text) > 2000:
            raise ValueError("prompt is too long (max 2000 characters)")

        return prompt_text

    def run_prompt(self, *, prompt: str) -> dict[str, str]:
        response = self.llm_client.generate(prompt=prompt, model=self.model)
        return {
            "prompt": prompt,
            "model": self.model,
            "response": response,
        }

    def handle_prompt(self, payload: dict[str, object]) -> tuple[dict[str, str], int]:
        try:
            prompt_text = self.normalize_prompt(payload)
        except ValueError as exc:
            return {"error": str(exc)}, 400

        try:
            result = self.run_prompt(prompt=prompt_text)
        except RuntimeError as exc:
            return {"error": str(exc)}, 502

        return result, 200
