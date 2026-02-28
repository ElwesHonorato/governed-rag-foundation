"""Object storage gateway builder for worker runtime."""

from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.settings import S3StorageSettings


class ObjectStorageGatewayBuilder:
    """Build object storage gateway from S3 runtime settings."""

    def __init__(self, *, s3_settings: S3StorageSettings) -> None:
        self.s3_settings = s3_settings

    def build(self) -> ObjectStorageGateway:
        """Build object storage gateway for one worker."""
        return ObjectStorageGateway(
            S3Client(
                endpoint_url=self.s3_settings.s3_endpoint,
                access_key=self.s3_settings.s3_access_key,
                secret_key=self.s3_settings.s3_secret_key,
                region_name=self.s3_settings.aws_region,
            )
        )
