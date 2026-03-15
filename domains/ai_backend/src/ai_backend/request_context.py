"""Request normalization for the AI backend WSGI app."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, cast

from ai_backend.http_types import WsgiEnv


@dataclass(slots=True)
class RequestContext:
    """Normalized WSGI request data."""

    method: str
    path: str
    body: dict[str, object]

    @classmethod
    def from_wsgi_env(cls, env: WsgiEnv) -> RequestContext:
        return cls(
            method=str(env.get("REQUEST_METHOD", "GET")).upper(),
            path=str(env.get("PATH_INFO", "/")),
            body=cls._read_json_body(env),
        )

    @staticmethod
    def _read_json_body(env: WsgiEnv) -> dict[str, object]:
        try:
            length = int(str(env.get("CONTENT_LENGTH") or "0"))
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        wsgi_input = cast(Any, env["wsgi.input"])
        raw = wsgi_input.read(length)
        if not raw:
            return {}
        return cast(dict[str, object], json.loads(raw.decode("utf-8")))
