
"""worker_chunk_text entrypoint.

Purpose:
- Bootstrap the chunking worker that converts processed documents into chunk artifacts.

What this module should do:
- Read queue and storage settings from environment.
- Create queue/storage gateways.
- Construct the chunking service and run it.

Best practices:
- Keep this file focused on composition, not transformation logic.
- Keep worker configuration centralized in `configs/constants.py`.
- Ensure queue contract and service wiring stay aligned when stages evolve.
"""

from pipeline_common.queue import StageQueue
from pipeline_common.startup import (
    build_lineage_emitter,
    build_object_storage,
    load_worker_runtime_settings,
)
from configs.constants import CHUNK_TEXT_LINEAGE_CONFIG, CHUNK_TEXT_PROCESSING_CONFIG
from services.worker_chunk_text_service import WorkerChunkTextService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    s3_settings, queue_settings, lineage_settings = load_worker_runtime_settings()
    processing_config = CHUNK_TEXT_PROCESSING_CONFIG
    lineage = build_lineage_emitter(
        lineage_settings=lineage_settings,
        lineage_config=CHUNK_TEXT_LINEAGE_CONFIG,
    )
    stage_queue = StageQueue(queue_settings.broker_url, queue_config=processing_config["queue"])
    object_storage = build_object_storage(s3_settings)
    WorkerChunkTextService(
        stage_queue=stage_queue,
        object_storage=object_storage,
        lineage=lineage,
        processing_config=processing_config,
    ).serve()


if __name__ == "__main__":
    run()
