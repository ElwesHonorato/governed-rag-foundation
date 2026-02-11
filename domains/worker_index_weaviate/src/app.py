
from pipeline_common.config import _required_env
from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.settings import QueueRuntimeSettings, S3StorageSettings
from pipeline_common.weaviate import ensure_schema
from configs.constants import INDEX_WEAVIATE_PROCESSING_CONFIG
from services.worker_index_weaviate_service import WorkerIndexWeaviateService


def run() -> None:
    s3_settings = S3StorageSettings.from_env()
    queue_settings = QueueRuntimeSettings.from_env()
    weaviate_url = _required_env("WEAVIATE_URL")
    processing_config = INDEX_WEAVIATE_PROCESSING_CONFIG
    stage_queue = StageQueue(queue_settings.broker_url, queue_config=processing_config["queue"])
    object_storage = ObjectStorageGateway(
        S3Client(
            endpoint_url=s3_settings.s3_endpoint,
            access_key=s3_settings.s3_access_key,
            secret_key=s3_settings.s3_secret_key,
            region_name=s3_settings.aws_region,
        )
    )
    ensure_schema(weaviate_url)
    WorkerIndexWeaviateService(
        stage_queue=stage_queue,
        storage=object_storage,
        storage_bucket=processing_config["storage"]["bucket"],
        weaviate_url=weaviate_url,
        poll_interval_seconds=queue_settings.poll_interval_seconds,
    ).serve()


if __name__ == "__main__":
    run()
