from dataclasses import dataclass

from .open_lineage.contracts import LineageEmitterConfig


@dataclass(frozen=True)
class DataHubFlowConfig:
    flow_platform: str
    flow_name: str
    flow_instance: str
    job_name: str

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


__all__ = ["LineageEmitterConfig", "DataHubFlowConfig"]
