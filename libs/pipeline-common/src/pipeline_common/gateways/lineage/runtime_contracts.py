from dataclasses import dataclass
from typing import Protocol

from pipeline_common.gateways.lineage.contracts import DataHubDataJobKey
from pipeline_common.gateways.lineage.contracts import DatasetPlatform, ResolvedDataHubFlowConfig


@dataclass
class CustomProperties:
    job_version: str
    error_message: str | None = None

    def dump(self) -> dict[str, str]:
        data = {"job_version": self.job_version}
        if self.error_message:
            data["error_message"] = self.error_message
        return data


@dataclass
class RunSpec:
    run_id: str
    custom_properties: CustomProperties
    inputs: list[str]
    outputs: list[str]


@dataclass(frozen=True)
class ActiveRunContext:
    run: RunSpec
    datajob_urn: str


@dataclass(frozen=True)
class DataHubRuntimeConnectionSettings:
    """DataHub connection settings used by runtime lineage clients."""

    server: str
    env: str
    token: str | None
    timeout_sec: float
    retry_max_times: int


@dataclass(frozen=True)
class DataHubLineageRuntimeConfig:
    """Typed DataHub client configuration for one worker stage."""

    connection_settings: DataHubRuntimeConnectionSettings
    data_job_key: DataHubDataJobKey


class LineageRuntimeGateway(Protocol):
    """Application port for runtime lineage emission operations."""

    @property
    def resolved_job_config(self) -> ResolvedDataHubFlowConfig:
        """Return resolved DataHub job metadata for the active worker."""

    def resolve_job_metadata(self) -> ResolvedDataHubFlowConfig:
        """Resolve and cache DataHub job metadata."""

    def start_run(self) -> RunSpec:
        """Start one lineage runtime run."""

    def add_input(self, name: str, platform: DatasetPlatform) -> str:
        """Add an input dataset URN to the active run."""

    def add_output(self, name: str, platform: DatasetPlatform) -> str:
        """Add an output dataset URN to the active run."""

    def complete_run(self) -> str:
        """Emit a completion event and return the DataProcessInstance URN."""

    def fail_run(self, error_message: str | None) -> str:
        """Emit a failure event and return the DataProcessInstance URN."""

    def abort_run(self) -> None:
        """Clear active run state without emitting terminal status."""
