"""Stage queue gateway factory for worker runtime."""

from typing import Any

from pipeline_common.gateways.queue import StageQueueGateway
from pipeline_common.gateways.queue.settings import QueueRuntimeSettings


class StageQueueGatewayFactory:
    """Create stage queue gateway from queue runtime settings and job config."""

    def __init__(self, *, queue_settings: QueueRuntimeSettings, queue_config: dict[str, Any]) -> None:
        self.queue_settings = queue_settings
        self.queue_config = queue_config

    def build(self) -> StageQueueGateway:
        """Create stage queue gateway for one worker."""
        return StageQueueGateway(
            self.queue_settings.broker_url,
            queue_config=self.queue_config,
        )
