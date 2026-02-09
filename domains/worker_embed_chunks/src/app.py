
import os

from pipeline_common.queue import StageQueue
from pipeline_common.s3 import S3Store, build_s3_client
from configs.configs import WorkerS3QueueLoopSettings
from services.worker_embed_chunks_service import WorkerEmbedChunksService


def run() -> None:
    settings = WorkerS3QueueLoopSettings.from_env()
    stage_queue = StageQueue(settings.broker_url)
    dimension = int(os.getenv("EMBEDDING_DIM", "32"))
    s3 = S3Store(
        build_s3_client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )
    WorkerEmbedChunksService(
        stage_queue=stage_queue,
        s3=s3,
        s3_bucket=settings.s3_bucket,
        poll_interval_seconds=settings.poll_interval_seconds,
        dimension=dimension,
    ).run_forever()


if __name__ == "__main__":
    run()
