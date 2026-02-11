
from pipeline_common.observability import Counters
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from configs.constants import S3_BUCKET
from configs.configs import WorkerS3LoopSettings
from services.worker_metrics_service import WorkerMetricsService


def run() -> None:
    settings = WorkerS3LoopSettings.from_env()
    counters = Counters().for_worker("worker_metrics")
    s3 = ObjectStorageGateway(
        S3Client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )
    WorkerMetricsService(
        counters=counters,
        s3=s3,
        s3_bucket=S3_BUCKET,
        poll_interval_seconds=settings.poll_interval_seconds,
    ).serve()


if __name__ == "__main__":
    run()
