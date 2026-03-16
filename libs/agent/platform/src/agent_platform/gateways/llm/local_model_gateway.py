"""Gateway adapter for model synthesis."""

from __future__ import annotations

from agent_platform.clients.llm.ollama_client import (
    LLMConnectionError,
    LLMHTTPError,
    LLMResponseError,
    OllamaClient,
)


class LocalModelGateway:
    """Delegates model synthesis to the configured Ollama client."""

    def __init__(self, *, llm_url: str, llm_model: str, timeout_seconds: int) -> None:
        if not llm_model.strip():
            raise ValueError("llm_model must be a non-empty string")
        self._client = OllamaClient(
            llm_url=llm_url,
            timeout_seconds=timeout_seconds,
            retries=0,
        )
        self._llm_model = llm_model.strip()

    def synthesize(self, prompt: str, context: dict[str, object]) -> str:
        try:
            return self._client.generate(
                prompt=prompt,
                model=self._llm_model,
                stream=False,
            )
        except LLMHTTPError as exc:
            raise ValueError(
                f"LLM HTTP {exc.status_code} for model '{self._llm_model}': {exc}"
            ) from exc
        except LLMConnectionError as exc:
            raise ValueError(
                f"LLM connection error for model '{self._llm_model}': {exc}"
            ) from exc
        except LLMResponseError as exc:
            raise ValueError(str(exc)) from exc
