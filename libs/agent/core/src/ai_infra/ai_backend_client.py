"""HTTP client for the AI backend API."""

from __future__ import annotations

import json
from urllib import error, request


class AiBackendClient:
    """Calls the ai_backend service for retrieval-grounded answers."""

    def __init__(self, *, base_url: str, timeout_seconds: int = 30) -> None:
        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError("ai_backend_url must be a non-empty string")
        self._base_url = base_url.strip().rstrip("/")
        self._timeout_seconds = timeout_seconds

    def query(self, payload: dict[str, object]) -> tuple[dict[str, object], int]:
        endpoint = f"{self._base_url}/rag/query"
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self._timeout_seconds) as response:
                raw = response.read().decode("utf-8", errors="replace")
                return self._parse_json(raw), response.status
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return self._parse_json(body), exc.code
        except error.URLError as exc:
            raise RuntimeError(
                f"AI backend connection error calling {endpoint}: {getattr(exc, 'reason', str(exc))}"
            ) from exc

    @staticmethod
    def _parse_json(raw: str) -> dict[str, object]:
        if not raw:
            return {}
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("AI backend response was not valid JSON") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("AI backend response JSON must be an object")
        return payload
