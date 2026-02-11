from pipeline_common.queue import StageQueue

from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.settings import QueueRuntimeSettings, S3StorageSettings
from configs.constants import PARSE_DOCUMENT_PROCESSING_CONFIG
from parsing.html import HtmlParser
from parsing.registry import ParserRegistry
from services.worker_parse_document_service import WorkerParseDocumentService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    s3_settings = S3StorageSettings.from_env()
    queue_settings = QueueRuntimeSettings.from_env()
    processing_config = PARSE_DOCUMENT_PROCESSING_CONFIG
    stage_queue = StageQueue(queue_settings.broker_url, queue_config=processing_config["queue"])
    parser_registry = ParserRegistry(parsers=[HtmlParser()])
    object_storage = ObjectStorageGateway(
        S3Client(
            endpoint_url=s3_settings.s3_endpoint,
            access_key=s3_settings.s3_access_key,
            secret_key=s3_settings.s3_secret_key,
            region_name=s3_settings.aws_region,
        )
    )
    WorkerParseDocumentService(
        stage_queue=stage_queue,
        object_storage=object_storage,
        processing_config=processing_config,
        parser_registry=parser_registry,
    ).serve()


if __name__ == "__main__":
    run()
