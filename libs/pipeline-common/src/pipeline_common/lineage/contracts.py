from dataclasses import dataclass, field

from .open_lineage.contracts import LineageEmitterConfig


@dataclass(frozen=True)
class DataHubFlowConfig:
    flow_id: str
    job_id: str
    flow_platform: str
    flow_name: str
    flow_instance: str
    job_name: str
    custom_properties: dict[str, str] = field(default_factory=dict)

    def flow_urn(self, flow_instance: str | None = None) -> str:
        """Build deterministic DataFlow URN from naming convention."""
        instance = flow_instance or self.flow_instance
        return (
            f"urn:li:dataFlow:({self.flow_platform},"
            f"{instance}.{self.flow_name},{instance})"
        )

    def job_urn(self, flow_instance: str | None = None) -> str:
        """Build deterministic DataJob URN from naming convention."""
        return f"urn:li:dataJob:({self.flow_urn(flow_instance)},{self.job_name})"

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


__all__ = ["LineageEmitterConfig", "DataHubFlowConfig"]
