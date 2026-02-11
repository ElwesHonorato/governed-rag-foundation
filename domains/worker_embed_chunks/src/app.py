
import os

from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.settings import QueueRuntimeSettings
from configs.constants import EMBED_CHUNKS_QUEUE, INDEX_WEAVIATE_QUEUE, S3_BUCKET
from configs.configs import WorkerS3QueueLoopSettings
from services.worker_embed_chunks_service import WorkerEmbedChunksService


def run() -> None:
    settings = WorkerS3QueueLoopSettings.from_env()
    queue_settings = QueueRuntimeSettings.from_env()
    embed_chunks_queue = StageQueue(
        queue_settings.broker_url,
        queue_name=EMBED_CHUNKS_QUEUE,
        default_pop_timeout_seconds=queue_settings.queue_pop_timeout_seconds,
    )
    index_weaviate_queue = StageQueue(
        queue_settings.broker_url,
        queue_name=INDEX_WEAVIATE_QUEUE,
        default_pop_timeout_seconds=queue_settings.queue_pop_timeout_seconds,
    )
    dimension = int(os.getenv("EMBEDDING_DIM", "32"))
    storage = ObjectStorageGateway(
        S3Client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )
    WorkerEmbedChunksService(
        embed_chunks_queue=embed_chunks_queue,
        index_weaviate_queue=index_weaviate_queue,
        storage=storage,
        storage_bucket=S3_BUCKET,
        poll_interval_seconds=settings.poll_interval_seconds,
        dimension=dimension,
    ).serve()


if __name__ == "__main__":
    run()
