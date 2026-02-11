import json
import time
from typing import Any

import pika
from pipeline_common.queue.contracts import StageQueueContract, WORKER_STAGE_QUEUES


class StageQueue:
    def __init__(
        self,
        broker_url: str,
        stage: str,
        stage_queues: dict[str, StageQueueContract] = WORKER_STAGE_QUEUES,
    ) -> None:
        self._enabled = pika is not None
        self._connection = pika.BlockingConnection(pika.URLParameters(broker_url)) if self._enabled else None
        self._channel = self._connection.channel() if self._connection else None
        self._initialize_stage_contract(stage=stage, stage_queues=stage_queues)

    def push(self, payload: dict[str, Any]) -> None:
        self._publish(self.produce, payload)

    def push_dlq(self, payload: dict[str, Any]) -> None:
        self._publish(self.dlq, payload)

    def pop(self, timeout_seconds: int) -> dict[str, Any] | None:
        return self._consume(self.consume, timeout_seconds=timeout_seconds)

    def _publish(self, queue_name: str, payload: dict[str, Any]) -> None:
        if not self._channel:
            return
        self._channel.queue_declare(queue=queue_name, durable=True)
        self._channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=json.dumps(payload, sort_keys=True),
            properties=pika.BasicProperties(delivery_mode=2),
        )

    def _consume(self, queue_name: str, timeout_seconds: int) -> dict[str, Any] | None:
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

    def _initialize_stage_contract(
        self,
        *,
        stage: str,
        stage_queues: dict[str, StageQueueContract],
    ) -> None:
        if stage not in stage_queues:
            raise ValueError(f"Unknown stage queue contract: {stage}")
        contract = stage_queues[stage]
        self.consume = contract["consume"]
        self.produce = contract["produce"]
        self.dlq = contract["dlq"]
