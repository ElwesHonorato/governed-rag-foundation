from enum import Enum
from dataclasses import dataclass, field


class DatasetPlatform(str, Enum):
    S3 = "s3"
    POSTGRES = "postgres"
    RABBITMQ = "rabbitmq"
    WEAVIATE = "weaviate"
    MYSQL = "mysql"
    KAFKA = "kafka"

    @property
    def platform(self) -> str:
        return self.value


@dataclass(frozen=True)
class DataHubDataJobKey:
    """Input key used to locate one DataHub DataJob."""

    flow_id: str
    job_id: str
    flow_platform: str


@dataclass(frozen=True)
class ResolvedDataHubFlowConfig:
    """Resolved flow/job metadata loaded from DataHub for one job key."""

    flow_id: str
    job_id: str
    flow_platform: str
    flow_instance: str
    custom_properties: dict[str, str] = field(default_factory=dict)

    @property
    def queue_consume(self) -> str | None:
        """Return consume queue configured for the stage, if any."""
        return self.custom_properties.get("queue.consume")

    @property
    def queue_produce(self) -> str | None:
        """Return produce queue configured for the stage, if any."""
        return self.custom_properties.get("queue.produce")

    @property
    def queue_dlq(self) -> str | None:
        """Return dead-letter queue configured for the stage, if any."""
        return self.custom_properties.get("queue.dlq")


__all__ = ["DatasetPlatform", "DataHubDataJobKey", "ResolvedDataHubFlowConfig"]
