
from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.settings import QueueRuntimeSettings
from configs.constants import CHUNK_TEXT_QUEUE, EMBED_CHUNKS_QUEUE, S3_BUCKET
from configs.configs import WorkerS3QueueLoopSettings
from services.worker_chunk_text_service import WorkerChunkTextService


def run() -> None:
    settings = WorkerS3QueueLoopSettings.from_env()
    queue_settings = QueueRuntimeSettings.from_env()
    chunk_text_queue = StageQueue(
        queue_settings.broker_url,
        queue_name=CHUNK_TEXT_QUEUE,
        default_pop_timeout_seconds=queue_settings.queue_pop_timeout_seconds,
    )
    embed_chunks_queue = StageQueue(
        queue_settings.broker_url,
        queue_name=EMBED_CHUNKS_QUEUE,
        default_pop_timeout_seconds=queue_settings.queue_pop_timeout_seconds,
    )
    storage = ObjectStorageGateway(
        S3Client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )
    WorkerChunkTextService(
        chunk_text_queue=chunk_text_queue,
        embed_chunks_queue=embed_chunks_queue,
        storage=storage,
        storage_bucket=S3_BUCKET,
        poll_interval_seconds=settings.poll_interval_seconds,
    ).serve()


if __name__ == "__main__":
    run()
