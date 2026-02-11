from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.settings import QueueRuntimeSettings, S3StorageSettings
from configs.constants import PROCESSING_CONFIG_DEFAULT, S3_BUCKET
from parsing.html import HtmlParser
from parsing.registry import ParserRegistry
from services.worker_parse_document_service import WorkerParseDocumentService


def run() -> None:
    s3_settings = S3StorageSettings.from_env()
    queue_settings = QueueRuntimeSettings.from_env()
    stage_queue = StageQueue(queue_settings.broker_url)
    parser_registry = ParserRegistry(parsers=[HtmlParser()])
    storage = ObjectStorageGateway(
        S3Client(
            endpoint_url=s3_settings.s3_endpoint,
            access_key=s3_settings.s3_access_key,
            secret_key=s3_settings.s3_secret_key,
            region_name=s3_settings.aws_region,
        )
    )
    WorkerParseDocumentService(
        stage_queue=stage_queue,
        storage=storage,
        storage_bucket=S3_BUCKET,
        poll_interval_seconds=queue_settings.poll_interval_seconds,
        processing_config=PROCESSING_CONFIG_DEFAULT,
        parser_registry=parser_registry,
    ).serve()


if __name__ == "__main__":
    run()
