from __future__ import annotations

import os
from dataclasses import dataclass


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
class WorkerS3LoopSettings:
    s3_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str
    aws_region: str
    poll_interval_seconds: int

    @classmethod
    def from_env(cls) -> WorkerS3LoopSettings:
        return cls(
            s3_endpoint=_required_env("S3_ENDPOINT"),
            s3_access_key=_required_env("S3_ACCESS_KEY"),
            s3_secret_key=_required_env("S3_SECRET_KEY"),
            s3_bucket=_required_env("S3_BUCKET"),
            aws_region=_optional_env("AWS_REGION", "us-east-1"),
            poll_interval_seconds=_required_int("WORKER_POLL_INTERVAL_SECONDS", 30),
        )


@dataclass(frozen=True)
class WorkerS3QueueLoopSettings:
    s3_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str
    aws_region: str
    poll_interval_seconds: int
    redis_url: str

    @classmethod
    def from_env(cls) -> WorkerS3QueueLoopSettings:
        return cls(
            s3_endpoint=_required_env("S3_ENDPOINT"),
            s3_access_key=_required_env("S3_ACCESS_KEY"),
            s3_secret_key=_required_env("S3_SECRET_KEY"),
            s3_bucket=_required_env("S3_BUCKET"),
            aws_region=_optional_env("AWS_REGION", "us-east-1"),
            poll_interval_seconds=_required_int("WORKER_POLL_INTERVAL_SECONDS", 30),
            redis_url=_required_env("REDIS_URL"),
        )


@dataclass(frozen=True)
class WorkerIndexWeaviateSettings:
    s3_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str
    aws_region: str
    poll_interval_seconds: int
    redis_url: str
    weaviate_url: str

    @classmethod
    def from_env(cls) -> WorkerIndexWeaviateSettings:
        return cls(
            s3_endpoint=_required_env("S3_ENDPOINT"),
            s3_access_key=_required_env("S3_ACCESS_KEY"),
            s3_secret_key=_required_env("S3_SECRET_KEY"),
            s3_bucket=_required_env("S3_BUCKET"),
            aws_region=_optional_env("AWS_REGION", "us-east-1"),
            poll_interval_seconds=_required_int("WORKER_POLL_INTERVAL_SECONDS", 30),
            redis_url=_required_env("REDIS_URL"),
            weaviate_url=_required_env("WEAVIATE_URL"),
        )
