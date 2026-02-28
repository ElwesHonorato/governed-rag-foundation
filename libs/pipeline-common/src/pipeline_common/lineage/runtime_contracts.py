from dataclasses import dataclass

from pipeline_common.lineage.contracts import DataHubDataJobKey


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
