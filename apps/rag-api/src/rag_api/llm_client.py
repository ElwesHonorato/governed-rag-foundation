from __future__ import annotations

import json
import time
from typing import Any
from urllib import error, request


class LLMError(RuntimeError):
    pass


class LLMHTTPError(LLMError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


class LLMConnectionError(LLMError):
    pass


class LLMResponseError(LLMError):
    pass


class OllamaClient:
    def __init__(self, *, llm_url: str, timeout_seconds: float = 30.0, retries: int = 1) -> None:
        if not isinstance(llm_url, str) or not llm_url.strip():
            raise ValueError("llm_url must be a non-empty string")
        self.llm_url = llm_url.strip().rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.retries = max(0, int(retries))

    def generate(
        self,
        *,
        prompt: str,
        model: str,
        options: dict[str, Any] | None = None,
        stream: bool = False,
    ) -> str:
        if not isinstance(prompt, str):
            raise ValueError("prompt must be a string")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model must be a non-empty string")
        if options is not None and not isinstance(options, dict):
            raise ValueError("options must be a dict when provided")
        if not isinstance(stream, bool):
            raise ValueError("stream must be a bool")

        payload: dict[str, Any] = {"model": model.strip(), "prompt": prompt, "stream": stream}
        if options is not None:
            payload["options"] = options

        data = self._post_with_retries(payload, model=model.strip())

        if data.get("error"):
            raise LLMResponseError(f"Ollama error for model '{model.strip()}': {data['error']}")

        response = data.get("response")
        if not isinstance(response, str):
            raise LLMResponseError("Ollama response is missing 'response' string field")
        return response

    def _post_with_retries(self, payload: dict[str, Any], *, model: str) -> dict[str, Any]:
        endpoint = f"{self.llm_url}/api/generate"
        total_attempts = self.retries + 1

        for attempt in range(1, total_attempts + 1):
            try:
                return self._post_once(endpoint, payload, model=model)
            except LLMConnectionError:
                if attempt == total_attempts:
                    raise
            except LLMHTTPError as exc:
                if exc.status_code not in {502, 503, 504} or attempt == total_attempts:
                    raise
            time.sleep(0.2 * attempt)

        raise LLMError("unexpected retry state")

    def _post_once(self, endpoint: str, payload: dict[str, Any], *, model: str) -> dict[str, Any]:
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                raw = resp.read()
        except error.HTTPError as exc:
            body_preview = self._truncate(self._read_error_body(exc), 500)
            raise LLMHTTPError(
                exc.code,
                f"HTTP {exc.code} from {endpoint} (model='{model}'): {body_preview}",
            ) from exc
        except error.URLError as exc:
            raise LLMConnectionError(
                f"Connection error calling {endpoint} (model='{model}'): {exc.reason}"
            ) from exc

        text = raw.decode("utf-8", errors="replace")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMResponseError(
                f"Invalid JSON from {endpoint}: {self._truncate(text, 500)}"
            ) from exc

        if not isinstance(data, dict):
            raise LLMResponseError("Ollama response JSON must be an object")
        return data

    @staticmethod
    def _read_error_body(exc: error.HTTPError) -> str:
        try:
            return exc.read().decode("utf-8", errors="replace")
        except Exception:
            return "<unavailable>"

    @staticmethod
    def _truncate(text: str, limit: int) -> str:
        return text if len(text) <= limit else text[:limit] + "...<truncated>"
