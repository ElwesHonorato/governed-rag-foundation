import json
import time
from typing import Any

import pika


class StageQueue:
    def __init__(
        self,
        broker_url: str,
        queue_name: str,
        default_pop_timeout_seconds: int = 1,
    ) -> None:
        self._enabled = pika is not None
        self._connection = pika.BlockingConnection(pika.URLParameters(broker_url)) if self._enabled else None
        self._channel = self._connection.channel() if self._connection else None
        self._queue_name = queue_name
        self._default_pop_timeout_seconds = default_pop_timeout_seconds

    def push(self, payload: dict[str, Any]) -> None:
        if not self._channel:
            return
        self._channel.queue_declare(queue=self._queue_name, durable=True)
        self._channel.basic_publish(
            exchange="",
            routing_key=self._queue_name,
            body=json.dumps(payload, sort_keys=True),
            properties=pika.BasicProperties(delivery_mode=2),
        )

    def pop(self, timeout_seconds: int | None = None) -> dict[str, Any] | None:
        if not self._channel:
            return None
        effective_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else self._default_pop_timeout_seconds
        )
        self._channel.queue_declare(queue=self._queue_name, durable=True)
        deadline = time.monotonic() + effective_timeout
        while time.monotonic() < deadline:
            method, _, body = self._channel.basic_get(queue=self._queue_name, auto_ack=False)
            if method and body:
                self._channel.basic_ack(method.delivery_tag)
                return json.loads(body)
            time.sleep(0.1)
        return None
