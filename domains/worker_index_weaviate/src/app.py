"""worker_index_weaviate entrypoint.

Purpose:
- Bootstrap the indexing worker that upserts embeddings into Weaviate.

What this module should do:
- Load storage/queue settings and required Weaviate URL.
- Ensure vector schema exists before starting the worker loop.
- Construct the indexing service and run it.

Best practices:
- Keep schema setup idempotent and startup-only.
- Keep this module orchestration-only; isolate indexing behavior in services.
- Validate required environment variables before opening long-running loops.
"""

from pipeline_common.config import _required_env
from pipeline_common.lineage.pipeline import DataHubPipelineJobs
from pipeline_common.startup import (
    InfrastructureFactory,
    RuntimeContextFactory,
)
from pipeline_common.weaviate import ensure_schema
from services.worker_index_weaviate_service import WorkerIndexWeaviateService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_index_weaviate"),
    )
    runtime = runtime_factory.runtime_context
    infra = InfrastructureFactory(runtime)
    lineage = infra.datahub_lineage_client
    raw_config = infra.job_properties
    job_config, queue_config = _extract_job_and_queue_config(raw_config)

    weaviate_url = _required_env("WEAVIATE_URL")
    stage_queue = infra.stage_queue
    object_storage = infra.object_storage
    ensure_schema(weaviate_url)
    WorkerIndexWeaviateService(
        stage_queue=stage_queue,
        object_storage=object_storage,
        lineage=lineage,
        processing_config={
            "poll_interval_seconds": int(job_config["poll_interval_seconds"]),
            "queue": queue_config,
            "storage": job_config["storage"],
        },
        weaviate_url=weaviate_url,
    ).serve()


def _extract_job_and_queue_config(expanded_config: dict) -> tuple[dict, dict]:
    """Return job and queue config sections from job properties."""
    job_config = expanded_config["job"]
    return job_config, job_config["queue"]


if __name__ == "__main__":
    run()
