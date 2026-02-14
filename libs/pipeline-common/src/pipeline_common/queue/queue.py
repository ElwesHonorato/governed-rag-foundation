import json

import logging
import time
from typing import Any, Callable

import pika
from pika.exceptions import AMQPError
from pipeline_common.queue.contracts import WorkerStageQueueContract

logger = logging.getLogger(__name__)


class StageQueue:
    """StageQueue type definition."""
    stage: str
    stage_queues: dict[str, WorkerStageQueueContract]
    timeout_seconds: int

    def __init__(
        self,
        broker_url: str,
        queue_config: dict[str, Any],
    ) -> None:
        """Initialize instance state and dependencies."""
        self._broker_url = broker_url
        self._enabled = pika is not None
        self._connection = None
        self._channel = None
        if self._enabled:
            self._connect()
        self._initialize_stage_contract(queue_config=queue_config)

    def push(self, payload: dict[str, Any]) -> None:
        """Execute push."""
        self._publish(self.produce, payload)

    def push_dlq(self, payload: dict[str, Any]) -> None:
        """Execute push dlq."""
        self._publish(self.dlq, payload)

    def pop(self, timeout_seconds: int | None = None) -> dict[str, Any] | None:
        """Execute pop."""
        consume_timeout = self.timeout_seconds if timeout_seconds is None else timeout_seconds
        return self._consume(self.consume, timeout_seconds=consume_timeout)

    def pop_message(self, timeout_seconds: int | None = None) -> dict[str, Any] | None:
        """Execute pop message."""
        payload = self.pop(timeout_seconds=timeout_seconds)
        if payload is None:
            return None
        return self.consume_contract(**payload)

    def push_produce_message(self, **payload: Any) -> None:
        """Execute push produce message."""
        self.push(self.produce_contract(**payload))

    def push_dlq_message(self, **payload: Any) -> None:
        """Execute push dlq message."""
        self.push_dlq(self.dlq_contract(**payload))

    def _publish(self, queue_name: str, payload: dict[str, Any]) -> None:
        """Internal helper for publish."""
        if not self._enabled:
            return
        body = json.dumps(payload, sort_keys=True)
        self._retry_operation(
            lambda: self._publish_once(queue_name=queue_name, body=body),
            op_name=f"publish:{queue_name}",
        )

    def _consume(self, queue_name: str, timeout_seconds: int) -> dict[str, Any] | None:
        """Internal helper for consume."""
        if not self._enabled:
            return None
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            try:
                self._ensure_channel()
                self._channel.queue_declare(queue=queue_name, durable=True)
                method, _, body = self._channel.basic_get(queue=queue_name, auto_ack=False)
                if method and body:
                    self._channel.basic_ack(method.delivery_tag)
                    return json.loads(body)
            except (AMQPError, OSError, RuntimeError):
                logger.exception("Queue consume failed; reconnecting and retrying")
                self._reconnect()
            time.sleep(0.1)
        return None

    def _publish_once(self, queue_name: str, body: str) -> None:
        """Publish payload body to one queue using the current channel."""
        self._ensure_channel()
        self._channel.queue_declare(queue=queue_name, durable=True)
        self._channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=body,
            properties=pika.BasicProperties(delivery_mode=2),
        )

    def _retry_operation(self, fn: Callable[[], None], op_name: str) -> None:
        """Run operation once, reconnect on AMQP failure, then retry once."""
        try:
            fn()
            return
        except (AMQPError, OSError, RuntimeError):
            logger.exception("Queue %s failed; reconnecting and retrying", op_name)
        self._reconnect()
        fn()

    def _connect(self) -> None:
        """Open broker connection and channel."""
        parameters = pika.URLParameters(self._broker_url)
        self._connection = pika.BlockingConnection(parameters)
        self._channel = self._connection.channel()

    def _close(self) -> None:
        """Close open channel/connection handles safely."""
        if self._channel is not None:
            try:
                self._channel.close()
            except Exception:
                pass
        if self._connection is not None:
            try:
                self._connection.close()
            except Exception:
                pass
        self._channel = None
        self._connection = None

    def _reconnect(self) -> None:
        """Recreate AMQP connection and channel."""
        if not self._enabled:
            return
        self._close()
        self._connect()

    def _ensure_channel(self) -> None:
        """Ensure there is an open AMQP channel."""
        if self._channel is None or self._connection is None:
            self._connect()
            return
        if self._connection.is_closed or self._channel.is_closed:
            self._reconnect()

    def _initialize_stage_contract(
        self,
        *,
        queue_config: dict[str, Any],
    ) -> None:
        """Internal helper for initialize stage contract."""
        self._load_stage_runtime_config(queue_config)
        stage_queue_contract = self._resolve_stage_contract()
        self._bind_stage_queue_names(stage_queue_contract)
        self._bind_stage_message_contracts(stage_queue_contract)

    def _load_stage_runtime_config(self, queue_config: dict[str, Any]) -> None:
        """Load stage identity, contract map, and timeout from config payload."""
        self.stage = str(queue_config["stage"])
        self.stage_queues = queue_config["stage_queues"]
        self.timeout_seconds = int(queue_config["queue_pop_timeout_seconds"])

    def _resolve_stage_contract(self) -> WorkerStageQueueContract:
        """Return queue contract for configured stage or raise on unknown stage."""
        if self.stage not in self.stage_queues:
            raise ValueError(f"Unknown stage queue contract: {self.stage}")
        return self.stage_queues[self.stage]

    def _bind_stage_queue_names(self, stage_queue_contract: WorkerStageQueueContract) -> None:
        """Bind consume/produce/dlq queue names from stage contract."""
        self.consume = stage_queue_contract["consume"]["queue_name"]
        self.produce = stage_queue_contract["produce"]["queue_name"]
        self.dlq = stage_queue_contract["dlq"]["queue_name"]

    def _bind_stage_message_contracts(self, stage_queue_contract: WorkerStageQueueContract) -> None:
        """Bind message contract constructors for consume/produce/dlq payloads."""
        self.consume_contract = stage_queue_contract["consume"]["queue_contract"]
        self.produce_contract = stage_queue_contract["produce"]["queue_contract"]
        self.dlq_contract = stage_queue_contract["dlq"]["queue_contract"]
