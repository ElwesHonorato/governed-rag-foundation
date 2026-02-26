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
    InfrastructureFactory,
    RuntimeContextFactory,
)
from services.worker_metrics_service import WorkerMetricsService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_metrics"),
    )
    runtime = runtime_factory.runtime_context
    infra = InfrastructureFactory(runtime)
    lineage = infra.datahub_lineage_client
    raw_config = infra.job_properties
    job_config = _extract_job_config(raw_config)

    counters = Counters().for_worker("worker_metrics")
    object_storage = infra.object_storage
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
