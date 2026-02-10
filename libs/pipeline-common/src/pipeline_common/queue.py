
import json
import time
from typing import Any

import pika


class StageQueue:
    def __init__(self, broker_url: str) -> None:
        self._enabled = pika is not None
        self._connection = pika.BlockingConnection(pika.URLParameters(broker_url)) if self._enabled else None
        self._channel = self._connection.channel() if self._connection else None

    def push(self, queue_name: str, payload: dict[str, Any]) -> None:
        if not self._channel:
            return
        self._channel.queue_declare(queue=queue_name, durable=True)
        self._channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=json.dumps(payload, sort_keys=True),
            properties=pika.BasicProperties(delivery_mode=2),
        )

    def pop(self, queue_name: str, timeout_seconds: int = 1) -> dict[str, Any] | None:
        if not self._channel:
            return None
        self._channel.queue_declare(queue=queue_name, durable=True)
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            method, _, body = self._channel.basic_get(queue=queue_name, auto_ack=False)
            if method and body:
                self._channel.basic_ack(method.delivery_tag)
                return json.loads(body)
            time.sleep(0.1)
        return None
