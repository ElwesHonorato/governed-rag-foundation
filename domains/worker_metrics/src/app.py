
from pipeline_common.observability import Counters
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from configs.constants import METRICS_PROCESSING_CONFIG
from configs.configs import WorkerS3LoopSettings
from services.worker_metrics_service import WorkerMetricsService


def run() -> None:
    settings = WorkerS3LoopSettings.from_env()
    processing_config = METRICS_PROCESSING_CONFIG
    counters = Counters().for_worker("worker_metrics")
    storage = ObjectStorageGateway(
        S3Client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )
    WorkerMetricsService(
        counters=counters,
        storage=storage,
        storage_bucket=processing_config["storage"]["bucket"],
        poll_interval_seconds=settings.poll_interval_seconds,
    ).serve()


if __name__ == "__main__":
    run()
