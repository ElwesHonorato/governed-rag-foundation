"""Stage queue infrastructure adapter.

Layer:
- Infrastructure adapter used by worker services.

Role:
- Wrap queue publish/consume operations for stage-based worker pipelines.

Design intent:
- Keep AMQP client mechanics isolated from worker services.

Non-goals:
- This module does not define business-level message schemas.
"""

import json

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import pika
from pika.exceptions import AMQPError

logger = logging.getLogger(__name__)


@dataclass
class ConsumedMessage:
    """A consumed queue message with explicit ack/nack controls."""

    payload: dict[str, Any]
    delivery_tag: int
    _queue: "StageQueueGateway" = field(repr=False)
    _settled: bool = field(default=False, init=False, repr=False)

    def ack(self) -> None:
        """Acknowledge the message once."""
        if self._settled:
            return
        self._queue._ack(self.delivery_tag)
        self._settled = True

    def nack(self, *, requeue: bool = True) -> None:
        """Negatively acknowledge the message once."""
        if self._settled:
            return
        self._queue._nack(self.delivery_tag, requeue=requeue)
        self._settled = True


class StageQueueGateway:
    """Runtime facade for stage queue interactions.

    Layer:
    - Infrastructure adapter facade.

    Dependencies:
    - pika/AMQP broker.
    - Runtime queue configuration parsed from job properties.

    Design intent:
    - Offer a narrow API for pushing/popping stage messages.

    Non-goals:
    - Does not provide exactly-once guarantees.
    - Does not abstract broker topology beyond direct queue names.
    """
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

    def pop_message(self, timeout_seconds: int | None = None) -> ConsumedMessage | None:
        """Execute pop message with explicit ack/nack control."""
        consume_timeout = self.timeout_seconds if timeout_seconds is None else timeout_seconds
        consumed = self._consume(self.consume, timeout_seconds=consume_timeout)
        if consumed is None:
            return None
        consumed.payload = self.consume_contract(**consumed.payload)
        return consumed

    def push_produce_message(self, **payload: Any) -> None:
        """Execute push produce message."""
        self.push(self.produce_contract(**payload))

    def push_dlq_message(self, **payload: Any) -> None:
        """Execute push dlq message."""
        self.push_dlq(self.dlq_contract(**payload))

    def _publish(self, queue_name: str, payload: dict[str, Any]) -> None:
        """Internal helper for publish."""
        if not queue_name:
            return
        if not self._enabled:
            return
        body = json.dumps(payload, sort_keys=True)
        self._retry_operation(
            lambda: self._publish_once(queue_name=queue_name, body=body),
            op_name=f"publish:{queue_name}",
        )

    def _consume(self, queue_name: str, timeout_seconds: int) -> ConsumedMessage | None:
        """Internal helper for consume."""
        if not queue_name:
            return None
        if not self._enabled:
            return None
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            try:
                self._ensure_channel()
                self._channel.queue_declare(queue=queue_name, durable=True)
                method, _, body = self._channel.basic_get(queue=queue_name, auto_ack=False)
                if method and body:
                    return ConsumedMessage(
                        payload=json.loads(body),
                        delivery_tag=int(method.delivery_tag),
                        _queue=self,
                    )
            except (AMQPError, OSError, RuntimeError):
                logger.exception("Queue consume failed; reconnecting and retrying")
                self._reconnect()
            time.sleep(0.1)
        return None

    def _ack(self, delivery_tag: int) -> None:
        """Acknowledge one consumed message."""
        self._retry_operation(
            lambda: self._ack_once(delivery_tag),
            op_name=f"ack:{delivery_tag}",
        )

    def _nack(self, delivery_tag: int, *, requeue: bool) -> None:
        """Negative-ack one consumed message."""
        self._retry_operation(
            lambda: self._nack_once(delivery_tag, requeue=requeue),
            op_name=f"nack:{delivery_tag}:requeue={requeue}",
        )

    def _ack_once(self, delivery_tag: int) -> None:
        """Ack one delivery tag on the current channel."""
        self._ensure_channel()
        self._channel.basic_ack(delivery_tag)

    def _nack_once(self, delivery_tag: int, *, requeue: bool) -> None:
        """Nack one delivery tag on the current channel."""
        self._ensure_channel()
        self._channel.basic_nack(delivery_tag, requeue=requeue)

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
        """Initialize queue names/contracts from direct runtime queue config."""
        self._load_stage_runtime_config(queue_config)
        self._bind_direct_queue_config(queue_config)

    def _load_stage_runtime_config(self, queue_config: dict[str, Any]) -> None:
        """Load queue timeout from config payload."""
        self.timeout_seconds = int(
            queue_config.get("queue_pop_timeout_seconds", queue_config.get("pop_timeout_seconds", 1))
        )

    def _bind_direct_queue_config(self, queue_config: dict[str, Any]) -> None:
        """Bind queue names/contracts from direct runtime config without stage contracts."""
        self.consume = str(queue_config.get("consume", ""))
        self.produce = str(queue_config.get("produce", ""))
        self.dlq = str(queue_config.get("dlq", ""))
        self.consume_contract = dict
        self.produce_contract = dict
        self.dlq_contract = dict
