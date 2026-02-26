"""worker_embed_chunks entrypoint.

Purpose:
- Bootstrap the embedding worker that transforms chunk artifacts into embedding payloads.

What this module should do:
- Load queue/storage settings and embedding dimension.
- Create queue/storage gateways.
- Construct the embedding service and run it.

Best practices:
- Treat this module as startup wiring only.
- Keep tunables (for example `EMBEDDING_DIM`) explicit and validated at startup.
- Keep downstream contract fields stable because later stages depend on them.
"""

import os

from pipeline_common.lineage.pipeline import DataHubPipelineJobs
from pipeline_common.startup import (
    InfrastructureFactory,
    RuntimeContextFactory,
)
from services.worker_embed_chunks_service import WorkerEmbedChunksService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_embed_chunks"),
    )
    runtime = runtime_factory.runtime_context
    infra = InfrastructureFactory(runtime)
    lineage = infra.datahub_lineage_client
    raw_config = infra.job_properties
    job_config, queue_config = _extract_job_and_queue_config(raw_config)

    stage_queue = infra.stage_queue
    dimension = int(job_config.get("dimension", os.getenv("EMBEDDING_DIM", "32")))
    object_storage = infra.object_storage
    WorkerEmbedChunksService(
        stage_queue=stage_queue,
        object_storage=object_storage,
        lineage=lineage,
        processing_config={
            "poll_interval_seconds": int(job_config["poll_interval_seconds"]),
            "queue": queue_config,
            "storage": job_config["storage"],
        },
        dimension=dimension,
    ).serve()


def _extract_job_and_queue_config(expanded_config: dict) -> tuple[dict, dict]:
    """Return job and queue config sections from job properties."""
    job_config = expanded_config["job"]
    return job_config, job_config["queue"]


if __name__ == "__main__":
    run()
