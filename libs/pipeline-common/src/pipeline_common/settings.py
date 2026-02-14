from dataclasses import dataclass


from pipeline_common.config import _optional_env, _required_env, _required_int


@dataclass(frozen=True)
class S3StorageSettings:
    """S3 connection and storage settings for workers."""

    s3_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    aws_region: str

    @classmethod
    def from_env(cls) -> "S3StorageSettings":
        """Execute from env."""
        return cls(
            s3_endpoint=_required_env("S3_ENDPOINT"),
            s3_access_key=_required_env("S3_ACCESS_KEY"),
            s3_secret_key=_required_env("S3_SECRET_KEY"),
            aws_region=_optional_env("AWS_REGION", "us-east-1"),
        )


@dataclass(frozen=True)
class QueueRuntimeSettings:
    """Queue runtime settings for workers."""

    broker_url: str
    queue_pop_timeout_seconds: int

    @classmethod
    def from_env(cls) -> "QueueRuntimeSettings":
        """Execute from env."""
        return cls(
            broker_url=_required_env("BROKER_URL"),
            queue_pop_timeout_seconds=_required_int("QUEUE_POP_TIMEOUT_SECONDS", 1),
        )
