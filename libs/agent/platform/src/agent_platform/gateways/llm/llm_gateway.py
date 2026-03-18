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

    def __init__(self, *, client: OllamaClient, timeout_seconds: float) -> None:
        self._client = client
        self._timeout_seconds = timeout_seconds

    def list_models(self) -> list[str]:
        return self._client.list_models(timeout_seconds=self._timeout_seconds)

    def resolve_model(self) -> str:
        available_models = self.list_models()
        if not available_models:
            raise ValueError("No LLM models are available from the configured backend.")
        if len(available_models) > 1:
            available_display = ", ".join(sorted(available_models))
            raise ValueError(
                "Multiple LLM models are available from the configured backend. "
                f"Expected exactly one model, found: {available_display}"
            )
        return available_models[0]

    def generate(self, prompt: str, model: str) -> str:
        try:
            return self._client.generate(
                prompt=prompt,
                model=model,
                stream=False,
                timeout_seconds=self._timeout_seconds,
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
            return self._client.chat(
                messages=messages,
                model=model,
                timeout_seconds=self._timeout_seconds,
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
