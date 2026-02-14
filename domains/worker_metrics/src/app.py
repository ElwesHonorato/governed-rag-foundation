
"""worker_metrics entrypoint.

Purpose:
- Bootstrap the metrics worker that emits stage counters for observability.

What this module should do:
- Load storage settings and initialize worker counters.
- Build object storage gateway.
- Construct the metrics service and run the polling loop.

Best practices:
- Keep metrics collection logic in the service layer, not in this entrypoint.
- Keep counter naming stable for downstream monitoring and dashboards.
- Keep startup deterministic and avoid hidden mutable globals.
"""

from pipeline_common.observability import Counters
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.settings import S3StorageSettings
from configs.constants import METRICS_PROCESSING_CONFIG
from services.worker_metrics_service import WorkerMetricsService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    s3_settings = S3StorageSettings.from_env()
    processing_config = METRICS_PROCESSING_CONFIG
    counters = Counters().for_worker("worker_metrics")
    object_storage = ObjectStorageGateway(
        S3Client(
            endpoint_url=s3_settings.s3_endpoint,
            access_key=s3_settings.s3_access_key,
            secret_key=s3_settings.s3_secret_key,
            region_name=s3_settings.aws_region,
        )
    )
    WorkerMetricsService(
        counters=counters,
        object_storage=object_storage,
        processing_config=processing_config,
    ).serve()


if __name__ == "__main__":
    run()
