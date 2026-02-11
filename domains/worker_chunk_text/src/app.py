
from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.settings import QueueRuntimeSettings, S3StorageSettings
from configs.constants import CHUNK_TEXT_PROCESSING_CONFIG
from services.worker_chunk_text_service import WorkerChunkTextService


def run() -> None:
    s3_settings = S3StorageSettings.from_env()
    queue_settings = QueueRuntimeSettings.from_env()
    processing_config = CHUNK_TEXT_PROCESSING_CONFIG
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
        storage=object_storage,
        processing_config=processing_config,
    ).serve()


if __name__ == "__main__":
    run()
