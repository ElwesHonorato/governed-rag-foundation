
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
from pipeline_common.queue import StageQueue
from pipeline_common.startup import (
    build_lineage_emitter,
    build_object_storage,
    load_worker_runtime_settings,
)
from pipeline_common.weaviate import ensure_schema
from configs.constants import INDEX_WEAVIATE_LINEAGE_CONFIG, INDEX_WEAVIATE_PROCESSING_CONFIG
from services.worker_index_weaviate_service import WorkerIndexWeaviateService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    s3_settings, queue_settings, lineage_settings = load_worker_runtime_settings()
    processing_config = INDEX_WEAVIATE_PROCESSING_CONFIG
    lineage = build_lineage_emitter(
        lineage_settings=lineage_settings,
        lineage_config=INDEX_WEAVIATE_LINEAGE_CONFIG,
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
