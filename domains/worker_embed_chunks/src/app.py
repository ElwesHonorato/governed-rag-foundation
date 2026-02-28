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
from pipeline_common.settings import DataHubSettings, QueueRuntimeSettings, S3StorageSettings
from pipeline_common.startup import (
    RuntimeContextFactory,
)
from services.worker_embed_chunks_service import WorkerEmbedChunksService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_embed_chunks"),
        datahub_settings=DataHubSettings.from_env(),
        s3_settings=S3StorageSettings.from_env(),
        queue_settings=QueueRuntimeSettings.from_env(),
    )
    lineage = runtime_factory.runtime_context.lineage_gateway
    raw_config = runtime_factory.runtime_context.job_properties
    job_config, queue_config = _extract_job_and_queue_config(raw_config)

    stage_queue = runtime_factory.runtime_context.stage_queue_gateway
    dimension = int(job_config.get("dimension", os.getenv("EMBEDDING_DIM", "32")))
    object_storage = runtime_factory.runtime_context.object_storage_gateway
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
