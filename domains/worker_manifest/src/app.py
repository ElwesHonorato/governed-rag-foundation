
"""worker_manifest entrypoint.

Purpose:
- Bootstrap the manifest worker that materializes per-document stage status metadata.

What this module should do:
- Load storage settings.
- Build object storage gateway.
- Construct the manifest service and start the polling loop.

Best practices:
- Keep this file minimal and orchestration-focused.
- Avoid embedding stage status rules here; keep those in service logic.
- Keep startup dependencies explicit so runtime behavior is predictable.
"""

from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.settings import S3StorageSettings
from configs.constants import MANIFEST_PROCESSING_CONFIG
from services.worker_manifest_service import WorkerManifestService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    s3_settings = S3StorageSettings.from_env()
    processing_config = MANIFEST_PROCESSING_CONFIG
    object_storage = ObjectStorageGateway(
        S3Client(
            endpoint_url=s3_settings.s3_endpoint,
            access_key=s3_settings.s3_access_key,
            secret_key=s3_settings.s3_secret_key,
            region_name=s3_settings.aws_region,
        )
    )
    WorkerManifestService(
        object_storage=object_storage,
        processing_config=processing_config,
    ).serve()


if __name__ == "__main__":
    run()
