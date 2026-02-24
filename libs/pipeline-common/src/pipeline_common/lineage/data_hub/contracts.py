from dataclasses import dataclass

from pipeline_common.lineage.contracts import DataHubDataJobKey


@dataclass(frozen=True)
class RunSpec:
    run_id: str
    job_version: str
    inputs: list[str]
    outputs: list[str]


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
