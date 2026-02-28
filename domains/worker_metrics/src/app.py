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

from pipeline_common.lineage.pipeline import DataHubPipelineJobs
from pipeline_common.observability import Counters
from pipeline_common.settings import DataHubSettings, QueueRuntimeSettings, S3StorageSettings
from pipeline_common.startup import (
    RuntimeContextFactory,
)
from services.worker_metrics_service import WorkerMetricsService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_metrics"),
        datahub_settings=DataHubSettings.from_env(),
        s3_settings=S3StorageSettings.from_env(),
        queue_settings=QueueRuntimeSettings.from_env(),
    )
    lineage = runtime_factory.runtime_context.lineage_gateway
    raw_config = runtime_factory.runtime_context.job_properties
    job_config = _extract_job_config(raw_config)

    counters = Counters().for_worker("worker_metrics")
    object_storage = runtime_factory.runtime_context.object_storage_gateway
    WorkerMetricsService(
        counters=counters,
        object_storage=object_storage,
        lineage=lineage,
        processing_config={
            "poll_interval_seconds": int(job_config["poll_interval_seconds"]),
            "storage": job_config["storage"],
        },
    ).serve()


def _extract_job_config(expanded_config: dict) -> dict:
    """Return job config section from job properties."""
    return expanded_config["job"]


if __name__ == "__main__":
    run()
