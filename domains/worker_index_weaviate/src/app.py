
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
from pipeline_common.queue import StageQueue
from pipeline_common.startup import (
    build_datahub_lineage_client,
    build_object_storage,
    load_runtime_settings,
)
from pipeline_common.weaviate import ensure_schema
from configs.constants import INDEX_WEAVIATE_PROCESSING_CONFIG
from services.worker_index_weaviate_service import WorkerIndexWeaviateService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    s3_settings, queue_settings, datahub_settings = load_runtime_settings()
    processing_config = INDEX_WEAVIATE_PROCESSING_CONFIG
    lineage = build_datahub_lineage_client(
        datahub_settings=datahub_settings,
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_index_weaviate"),
    )
    weaviate_url = _required_env("WEAVIATE_URL")
    stage_queue = StageQueue(queue_settings.broker_url, queue_config=processing_config["queue"])
    object_storage = build_object_storage(s3_settings)
    ensure_schema(weaviate_url)
    WorkerIndexWeaviateService(
        stage_queue=stage_queue,
        object_storage=object_storage,
        lineage=lineage,
        processing_config=processing_config,
        weaviate_url=weaviate_url,
    ).serve()


if __name__ == "__main__":
    run()
