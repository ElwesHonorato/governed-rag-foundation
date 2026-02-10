from dataclasses import dataclass
import os


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} is not configured")
    return value.strip()


def _optional_env(name: str, default: str) -> str:
    value = os.getenv(name, default)
    return value.strip() or default


def _required_int(name: str, default: int) -> int:
    raw = _optional_env(name, str(default))
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return parsed


@dataclass(frozen=True)
class S3StorageSettings:
    """S3 connection and storage settings for workers."""

    s3_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    aws_region: str

    @classmethod
    def from_env(cls) -> "S3StorageSettings":
        return cls(
            s3_endpoint=_required_env("S3_ENDPOINT"),
            s3_access_key=_required_env("S3_ACCESS_KEY"),
            s3_secret_key=_required_env("S3_SECRET_KEY"),
            aws_region=_optional_env("AWS_REGION", "us-east-1"),
        )


@dataclass(frozen=True)
class QueueRuntimeSettings:
    """Queue and poll-loop settings for workers."""

    broker_url: str
    poll_interval_seconds: int

    @classmethod
    def from_env(cls) -> "QueueRuntimeSettings":
        return cls(
            broker_url=_required_env("BROKER_URL"),
            poll_interval_seconds=_required_int("WORKER_POLL_INTERVAL_SECONDS", 30),
        )
