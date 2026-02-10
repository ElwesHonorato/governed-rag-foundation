
from pipeline_common.s3 import ObjectStorageGateway, build_s3_client
from configs.configs import WorkerS3LoopSettings
from services.worker_manifest_service import WorkerManifestService


def run() -> None:
    settings = WorkerS3LoopSettings.from_env()
    s3 = ObjectStorageGateway(
        build_s3_client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )
    WorkerManifestService(
        s3=s3,
        s3_bucket=settings.s3_bucket,
        poll_interval_seconds=settings.poll_interval_seconds,
    ).serve()


if __name__ == "__main__":
    run()
