
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.settings import S3StorageSettings
from configs.constants import MANIFEST_PROCESSING_CONFIG
from services.worker_manifest_service import WorkerManifestService


def run() -> None:
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
        storage=object_storage,
        storage_bucket=processing_config["storage"]["bucket"],
        poll_interval_seconds=processing_config["poll_interval_seconds"],
    ).serve()


if __name__ == "__main__":
    run()
