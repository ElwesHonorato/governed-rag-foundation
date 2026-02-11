import json
import time
from typing import Any

import pika
from pipeline_common.queue.contracts import WorkerStageQueueContract


class StageQueue:
    stage: str
    stage_queues: dict[str, WorkerStageQueueContract]
    timeout_seconds: int

    def __init__(
        self,
        broker_url: str,
        queue_config: dict[str, Any],
    ) -> None:
        self._enabled = pika is not None
        self._connection = pika.BlockingConnection(pika.URLParameters(broker_url)) if self._enabled else None
        self._channel = self._connection.channel() if self._connection else None
        self._initialize_stage_contract(queue_config=queue_config)

    def push(self, payload: dict[str, Any]) -> None:
        self._publish(self.produce, payload)

    def push_dlq(self, payload: dict[str, Any]) -> None:
        self._publish(self.dlq, payload)

    def pop(self, timeout_seconds: int | None = None) -> dict[str, Any] | None:
        consume_timeout = self.timeout_seconds if timeout_seconds is None else timeout_seconds
        return self._consume(self.consume, timeout_seconds=consume_timeout)

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
        queue_config: dict[str, Any],
    ) -> None:
        self.stage = str(queue_config["stage"])
        self.stage_queues = queue_config["stage_queues"]
        self.timeout_seconds = int(queue_config["queue_pop_timeout_seconds"])
        if self.stage not in self.stage_queues:
            raise ValueError(f"Unknown stage queue contract: {self.stage}")
        stage_queue_contract = self.stage_queues[self.stage]
        self.consume = stage_queue_contract["consume"]["queue_name"]
        self.produce = stage_queue_contract["produce"]["queue_name"]
        self.dlq = stage_queue_contract["dlq"]["queue_name"]
        self.consume_contract = stage_queue_contract["consume"]["queue_contract"]
        self.produce_contract = stage_queue_contract["produce"]["queue_contract"]
        self.dlq_contract = stage_queue_contract["dlq"]["queue_contract"]
