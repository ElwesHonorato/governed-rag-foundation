from enum import Enum
from dataclasses import dataclass, field

from .urns import DataHubUrnFactory


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

    def flow_urn(self, flow_instance: str | None = None) -> str:
        """Build deterministic DataFlow URN from naming convention."""
        instance = flow_instance or self.flow_instance
        return DataHubUrnFactory.flow_urn(
            flow_platform=self.flow_platform,
            flow_id=self.flow_id,
            flow_instance=instance,
        )

    def job_urn(self, flow_instance: str | None = None) -> str:
        """Build deterministic DataJob URN from naming convention."""
        instance = flow_instance or self.flow_instance
        return DataHubUrnFactory.job_urn(
            flow_platform=self.flow_platform,
            flow_id=self.flow_id,
            flow_instance=instance,
            job_id=self.job_id,
        )

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
