
from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.settings import QueueRuntimeSettings
from configs.constants import QUEUE_CONFIG_DEFAULT, S3_BUCKET
from configs.configs import WorkerS3QueueLoopSettings
from services.worker_chunk_text_service import WorkerChunkTextService


def run() -> None:
    settings = WorkerS3QueueLoopSettings.from_env()
    queue_settings = QueueRuntimeSettings.from_env()
    stage_queue = StageQueue(queue_settings.broker_url, queue_config=QUEUE_CONFIG_DEFAULT)
    storage = ObjectStorageGateway(
        S3Client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )
    WorkerChunkTextService(
        stage_queue=stage_queue,
        storage=storage,
        storage_bucket=S3_BUCKET,
        poll_interval_seconds=settings.poll_interval_seconds,
        queue_pop_timeout_seconds=queue_settings.queue_pop_timeout_seconds,
    ).serve()


if __name__ == "__main__":
    run()
