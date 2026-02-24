from dataclasses import dataclass
from typing import Any

from pipeline_common.lineage.contracts import DataHubDataJobKey


@dataclass(frozen=True)
class RunSpec:
    run_id: str
    attempt: int
    job_version: str
    inputs: list[str]
    outputs: list[str]


@dataclass(frozen=True)
class DataHubLineageRuntimeConfig:
    """Typed DataHub client configuration for one worker stage."""

    bootstrap_settings: dict[str, Any]
    data_job_key: DataHubDataJobKey
