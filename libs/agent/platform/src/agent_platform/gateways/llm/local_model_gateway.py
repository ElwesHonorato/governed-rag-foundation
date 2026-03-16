"""HTTP-backed synthesis adapter."""

from __future__ import annotations

import json
from urllib import error, request


class LocalModelGateway:
    """Calls the configured Ollama-compatible generation endpoint."""

    def __init__(self, *, llm_url: str, llm_model: str, timeout_seconds: int) -> None:
        if not llm_url.strip():
            raise ValueError("llm_url must be a non-empty string")
        if not llm_model.strip():
            raise ValueError("llm_model must be a non-empty string")
        self._endpoint = f"{llm_url.rstrip('/')}/api/generate"
        self._llm_model = llm_model.strip()
        self._timeout_seconds = timeout_seconds

    def synthesize(self, prompt: str, context: dict[str, object]) -> str:
        payload = {
            "model": self._llm_model,
            "prompt": prompt,
            "stream": False,
        }
        req = request.Request(
            self._endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self._timeout_seconds) as response:
                raw = response.read()
        except error.HTTPError as exc:
            body_preview = exc.read().decode("utf-8", errors="replace")
            raise ValueError(
                f"LLM HTTP {exc.code} from {self._endpoint} for model '{self._llm_model}': {body_preview[:500]}"
            ) from exc
        except (error.URLError, TimeoutError) as exc:
            raise ValueError(
                f"LLM connection error calling {self._endpoint} for model '{self._llm_model}': "
                f"{getattr(exc, 'reason', str(exc))}"
            ) from exc

        try:
            payload = json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError as exc:
            raise ValueError("LLM response was not valid JSON.") from exc
        if not isinstance(payload, dict):
            raise ValueError("LLM response JSON must be an object.")
        if payload.get("error"):
            raise ValueError(f"LLM backend error for model '{self._llm_model}': {payload['error']}")
        response_text = payload.get("response")
        if not isinstance(response_text, str) or not response_text.strip():
            raise ValueError("LLM response is missing 'response' text.")
        return response_text
