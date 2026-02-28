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
    RuntimeContextFactory,
)
from pipeline_common.weaviate import ensure_schema
from services.worker_index_weaviate_service import WorkerIndexWeaviateService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_index_weaviate"),
    )
    lineage = runtime_factory.runtime_context.lineage_gateway
    raw_config = runtime_factory.runtime_context.job_properties
    job_config, queue_config = _extract_job_and_queue_config(raw_config)

    weaviate_url = _required_env("WEAVIATE_URL")
    stage_queue = runtime_factory.runtime_context.stage_queue_gateway
    object_storage = runtime_factory.runtime_context.object_storage_gateway
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
