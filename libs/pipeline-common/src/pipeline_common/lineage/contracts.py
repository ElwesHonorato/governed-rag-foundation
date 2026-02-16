from dataclasses import dataclass

from pipeline_common.config import JobStageName
from pipeline_common.lineage.constants import LineageNamespace


@dataclass(frozen=True)
class LineageEmitterConfig:
    """Static lineage metadata for one worker/job stage."""

    namespace: str | LineageNamespace
    producer: str
    job_stage: JobStageName | None = None
    timeout_seconds: float = 3.0
