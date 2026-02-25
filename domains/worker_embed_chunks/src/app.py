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
    build_datahub_lineage_client,
    build_object_storage,
    build_stage_queue,
    expand_dot_properties,
    load_runtime_settings,
)
from services.worker_embed_chunks_service import WorkerEmbedChunksService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    s3_settings, queue_settings, datahub_settings = load_runtime_settings()
    lineage = build_datahub_lineage_client(
        datahub_settings=datahub_settings,
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_embed_chunks"),
    )
    raw_config = expand_dot_properties(lineage.resolved_job_config.custom_properties)
    embed_config, queue_config = _extract_embed_and_queue_config(raw_config)

    stage_queue = build_stage_queue(
        broker_url=queue_settings.broker_url,
        queue_config=queue_config,
    )
    dimension = int(embed_config.get("dimension", os.getenv("EMBEDDING_DIM", "32")))
    object_storage = build_object_storage(s3_settings)
    WorkerEmbedChunksService(
        stage_queue=stage_queue,
        object_storage=object_storage,
        lineage=lineage,
        processing_config={
            "poll_interval_seconds": int(embed_config["poll_interval_seconds"]),
            "queue": queue_config,
            "storage": embed_config["storage"],
        },
        dimension=dimension,
    ).serve()


def _extract_embed_and_queue_config(expanded_config: dict) -> tuple[dict, dict]:
    """Return embed and queue config sections from expanded properties."""
    return expanded_config["embed"], expanded_config["queue"]


if __name__ == "__main__":
    run()
