from dataclasses import dataclass

from pipeline_common.helpers.config import _optional_env, _required_env


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
