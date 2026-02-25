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
from pipeline_common.startup import (
    build_datahub_lineage_client,
    build_object_storage,
    expand_dot_properties,
    load_runtime_settings,
)
from services.worker_metrics_service import WorkerMetricsService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    s3_settings, _, datahub_settings = load_runtime_settings()
    lineage = build_datahub_lineage_client(
        datahub_settings=datahub_settings,
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_metrics"),
    )
    raw_config = expand_dot_properties(lineage.resolved_job_config.custom_properties)
    metrics_config = raw_config["metrics"]

    counters = Counters().for_worker("worker_metrics")
    object_storage = build_object_storage(s3_settings)
    WorkerMetricsService(
        counters=counters,
        object_storage=object_storage,
        lineage=lineage,
        processing_config={
            "poll_interval_seconds": int(metrics_config["poll_interval_seconds"]),
            "storage": metrics_config["storage"],
        },
    ).serve()


if __name__ == "__main__":
    run()
