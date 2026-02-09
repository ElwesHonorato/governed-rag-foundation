from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    s3_endpoint: str = field(init=False)
    s3_access_key: str = field(init=False)
    s3_secret_key: str = field(init=False)
    s3_bucket: str = field(init=False)
    weaviate_url: str = field(init=False)
    redis_url: str = field(init=False)
    marquez_url: str = field(init=False)
    aws_region: str = field(init=False)
    poll_interval_seconds: int = field(init=False)

    def __post_init__(self) -> None:
        self.s3_endpoint = self._required_env("S3_ENDPOINT")
        self.s3_access_key = self._required_env("S3_ACCESS_KEY")
        self.s3_secret_key = self._required_env("S3_SECRET_KEY")
        self.s3_bucket = self._required_env("S3_BUCKET")
        self.weaviate_url = self._required_env("WEAVIATE_URL")
        self.redis_url = self._required_env("REDIS_URL")
        self.marquez_url = self._required_env("MARQUEZ_URL")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1").strip() or "us-east-1"
        self.poll_interval_seconds = int(os.getenv("WORKER_POLL_INTERVAL_SECONDS", "30"))

    def _required_env(self, name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"{name} is not configured")
        return value.strip()
