from dataclasses import dataclass, replace

from pipeline_common.config import JobStageName
from pipeline_common.lineage.data_hub.constants import DataHubStageFlowConfig


@dataclass(frozen=True)
class LineageEmitterConfig:
    """Static lineage metadata for one worker/job stage."""

    namespace: str
    producer: str
    job_stage: JobStageName | None = None
    dataset_namespace: str | None = None
    timeout_seconds: float = 3.0
    flow_name: str | None = None
    flow_platform: str = "custom"
    flow_instance: str = "PROD"


@dataclass(frozen=True)
class RunSpec:
    run_id: str
    attempt: int
    job_version: str
    inputs: list[str]
    outputs: list[str]


@dataclass(frozen=True)
class ClientConfig:
    """Typed DataHub client configuration for one worker stage."""

    server: str
    stage: DataHubStageFlowConfig
    token: str | None = None
    env: str = "PROD"

    def with_server_env(self, *, server: str, env: str) -> "ClientConfig":
        """Return a copy overriding runtime server/environment values."""
        return replace(self, server=server, env=env)
