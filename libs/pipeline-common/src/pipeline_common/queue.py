from __future__ import annotations

import json
from typing import Any

try:
    import redis
except Exception:  # pragma: no cover
    redis = None


class StageQueue:
    def __init__(self, redis_url: str) -> None:
        self._enabled = redis is not None
        self._client = redis.Redis.from_url(redis_url, decode_responses=True) if self._enabled else None

    def push(self, queue_name: str, payload: dict[str, Any]) -> None:
        if not self._client:
            return
        self._client.rpush(queue_name, json.dumps(payload, sort_keys=True))

    def pop(self, queue_name: str, timeout_seconds: int = 1) -> dict[str, Any] | None:
        if not self._client:
            return None
        value = self._client.blpop(queue_name, timeout=timeout_seconds)
        if not value:
            return None
        _, raw_payload = value
        return json.loads(raw_payload)
