
import os

from pipeline_common.queue import StageQueue
from pipeline_common.s3 import ObjectStorageGateway, S3Client
from configs.constants import S3_BUCKET
from configs.configs import WorkerS3QueueLoopSettings
from services.worker_embed_chunks_service import WorkerEmbedChunksService


def run() -> None:
    settings = WorkerS3QueueLoopSettings.from_env()
    stage_queue = StageQueue(settings.broker_url)
    dimension = int(os.getenv("EMBEDDING_DIM", "32"))
    s3 = ObjectStorageGateway(
        S3Client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )
    WorkerEmbedChunksService(
        stage_queue=stage_queue,
        s3=s3,
        s3_bucket=S3_BUCKET,
        poll_interval_seconds=settings.poll_interval_seconds,
        dimension=dimension,
    ).serve()


if __name__ == "__main__":
    run()
