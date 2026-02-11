from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.settings import QueueRuntimeSettings, S3StorageSettings
from configs.constants import PROCESSING_CONFIG_DEFAULT
from parsing.html import HtmlParser
from parsing.registry import ParserRegistry
from services.worker_parse_document_service import WorkerParseDocumentService


def run() -> None:
    s3_settings = S3StorageSettings.from_env()
    queue_settings = QueueRuntimeSettings.from_env()
    stage_queue = StageQueue(
        queue_settings.broker_url,
        default_pop_timeout_seconds=queue_settings.queue_pop_timeout_seconds,
    )
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
        processing_config=PROCESSING_CONFIG_DEFAULT,
        parser_registry=parser_registry,
    ).serve()


if __name__ == "__main__":
    run()
