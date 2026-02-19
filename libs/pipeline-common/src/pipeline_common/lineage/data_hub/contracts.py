from dataclasses import dataclass

from pipeline_common.config import JobStageName


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
