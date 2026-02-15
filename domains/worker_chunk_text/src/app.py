
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
from pipeline_common.lineage import LineageEmitter
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.settings import LineageRuntimeSettings, QueueRuntimeSettings, S3StorageSettings
from configs.constants import CHUNK_TEXT_PROCESSING_CONFIG
from services.worker_chunk_text_service import WorkerChunkTextService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    s3_settings = S3StorageSettings.from_env()
    queue_settings = QueueRuntimeSettings.from_env()
    lineage_settings = LineageRuntimeSettings.from_env()
    processing_config = CHUNK_TEXT_PROCESSING_CONFIG
    lineage = LineageEmitter(
        lineage_settings=lineage_settings,
        lineage_config=processing_config["lineage"],
    )
    stage_queue = StageQueue(queue_settings.broker_url, queue_config=processing_config["queue"])
    object_storage = ObjectStorageGateway(
        S3Client(
            endpoint_url=s3_settings.s3_endpoint,
            access_key=s3_settings.s3_access_key,
            secret_key=s3_settings.s3_secret_key,
            region_name=s3_settings.aws_region,
        )
    )
    WorkerChunkTextService(
        stage_queue=stage_queue,
        object_storage=object_storage,
        lineage=lineage,
        processing_config=processing_config,
    ).serve()


if __name__ == "__main__":
    run()
