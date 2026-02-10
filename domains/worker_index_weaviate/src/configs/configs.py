
from dataclasses import dataclass

from pipeline_common.config import _optional_env, _required_env, _required_int


@dataclass(frozen=True)
class WorkerIndexWeaviateSettings:
    s3_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    aws_region: str
    poll_interval_seconds: int
    broker_url: str
    weaviate_url: str

    @classmethod
    def from_env(cls) -> "WorkerIndexWeaviateSettings":
        return cls(
            s3_endpoint=_required_env("S3_ENDPOINT"),
            s3_access_key=_required_env("S3_ACCESS_KEY"),
            s3_secret_key=_required_env("S3_SECRET_KEY"),
            aws_region=_optional_env("AWS_REGION", "us-east-1"),
            poll_interval_seconds=_required_int("WORKER_POLL_INTERVAL_SECONDS", 30),
            broker_url=_required_env("BROKER_URL"),
            weaviate_url=_required_env("WEAVIATE_URL"),
        )
