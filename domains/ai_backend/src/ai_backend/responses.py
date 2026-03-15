"""JSON response construction for the AI backend."""

from __future__ import annotations

import json
from http import HTTPStatus

from ai_backend.http_types import JsonValue, StartResponse


class JsonResponse:
    """JSON HTTP response."""

    def __init__(self, *, payload: JsonValue, status: HTTPStatus) -> None:
        self.payload = payload
        self.status = status

    def to_wsgi(self, start_response: StartResponse) -> list[bytes]:
        response_bytes = json.dumps(self.payload, indent=2).encode("utf-8")
        start_response(
            f"{self.status.value} {self.status.phrase}",
            [
                ("Content-Type", "application/json"),
                ("Content-Length", str(len(response_bytes))),
            ],
        )
        return [response_bytes]
