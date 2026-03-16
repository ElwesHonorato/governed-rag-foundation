"""Gateway adapter for LLM operations backed by the configured LLM client."""

from __future__ import annotations

from agent_platform.clients.llm.ollama_client import (
    LLMConnectionError,
    LLMHTTPError,
    LLMResponseError,
    OllamaClient,
)


class LLMGateway:
    """Expose app-facing LLM operations over the configured LLM client."""

    def __init__(self, *, client: OllamaClient) -> None:
        self._client = client

    def generate(self, prompt: str, model: str) -> str:
        try:
            return self._client.generate(
                prompt=prompt,
                model=model,
                stream=False,
            )
        except LLMHTTPError as exc:
            raise ValueError(
                f"LLM HTTP {exc.status_code} for model '{model}': {exc}"
            ) from exc
        except LLMConnectionError as exc:
            raise ValueError(
                f"LLM connection error for model '{model}': {exc}"
            ) from exc
        except LLMResponseError as exc:
            raise ValueError(str(exc)) from exc

    def chat(self, *, messages: list[dict[str, str]], model: str) -> str:
        try:
            return self._client.chat(messages=messages, model=model)
        except LLMHTTPError as exc:
            raise ValueError(
                f"LLM HTTP {exc.status_code} for model '{model}': {exc}"
            ) from exc
        except LLMConnectionError as exc:
            raise ValueError(
                f"LLM connection error for model '{model}': {exc}"
            ) from exc
        except LLMResponseError as exc:
            raise ValueError(str(exc)) from exc
