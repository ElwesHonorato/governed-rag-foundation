
from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.weaviate import ensure_schema
from configs.constants import S3_BUCKET
from configs.configs import WorkerIndexWeaviateSettings
from services.worker_index_weaviate_service import WorkerIndexWeaviateService


def run() -> None:
    settings = WorkerIndexWeaviateSettings.from_env()
    stage_queue = StageQueue(settings.broker_url)
    s3 = ObjectStorageGateway(
        S3Client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )
    ensure_schema(settings.weaviate_url)
    WorkerIndexWeaviateService(
        stage_queue=stage_queue,
        s3=s3,
        s3_bucket=S3_BUCKET,
        weaviate_url=settings.weaviate_url,
        poll_interval_seconds=settings.poll_interval_seconds,
    ).serve()


if __name__ == "__main__":
    run()
