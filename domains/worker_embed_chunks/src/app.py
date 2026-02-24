
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
from pipeline_common.queue import StageQueue
from pipeline_common.startup import (
    build_datahub_lineage_client,
    build_object_storage,
    load_runtime_settings,
)
from configs.constants import EMBED_CHUNKS_PROCESSING_CONFIG
from services.worker_embed_chunks_service import WorkerEmbedChunksService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    s3_settings, queue_settings, datahub_settings = load_runtime_settings()
    processing_config = EMBED_CHUNKS_PROCESSING_CONFIG
    lineage = build_datahub_lineage_client(
        datahub_settings=datahub_settings,
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_embed_chunks"),
    )
    stage_queue = StageQueue(queue_settings.broker_url, queue_config=processing_config["queue"])
    dimension = int(os.getenv("EMBEDDING_DIM", "32"))
    object_storage = build_object_storage(s3_settings)
    WorkerEmbedChunksService(
        stage_queue=stage_queue,
        object_storage=object_storage,
        lineage=lineage,
        processing_config=processing_config,
        dimension=dimension,
    ).serve()


if __name__ == "__main__":
    run()
