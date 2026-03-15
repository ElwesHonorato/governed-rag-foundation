"""WSGI request normalization for the AI backend."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, cast

from ai_backend.http_types import WsgiEnv


@dataclass(slots=True)
class NormalizedRequest:
    """Normalized WSGI request data."""

    method: str
    path: str
    body: dict[str, object]


class WsgiRequestNormalizer:
    """Translate the raw WSGI environment into a normalized request object."""

    def normalize(self, env: WsgiEnv) -> NormalizedRequest:
        return NormalizedRequest(
            method=str(env.get("REQUEST_METHOD", "GET")).upper(),
            path=str(env.get("PATH_INFO", "/")),
            body=self._read_json_body(env),
        )

    def _read_json_body(self, env: WsgiEnv) -> dict[str, object]:
        try:
            content_length = int(str(env.get("CONTENT_LENGTH") or "0"))
        except ValueError:
            content_length = 0
        if content_length <= 0:
            return {}
        wsgi_input = cast(Any, env["wsgi.input"])
        raw_body = wsgi_input.read(content_length)
        if not raw_body:
            return {}
        return cast(dict[str, object], json.loads(raw_body.decode("utf-8")))
