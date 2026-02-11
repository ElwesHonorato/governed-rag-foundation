from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from configs.constants import HTML_EXTENSIONS, INCOMING_PREFIX, PARSE_QUEUE, RAW_PREFIX, S3_BUCKET
from configs.configs import WorkerS3QueueLoopSettings
from services.scan_cycle_processor import StorageScanCycleProcessor
from services.worker_scan_service import WorkerScanService


def run() -> None:
    settings = WorkerS3QueueLoopSettings.from_env()
    parse_queue = StageQueue(settings.broker_url, queue_name=PARSE_QUEUE)
    storage = ObjectStorageGateway(
        S3Client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )
    storage.bootstrap_bucket_prefixes(S3_BUCKET)
    processor = StorageScanCycleProcessor(
        storage=storage,
        parse_queue=parse_queue,
        bucket=S3_BUCKET,
        source_prefix=INCOMING_PREFIX,
        destination_prefix=RAW_PREFIX,
        extensions=HTML_EXTENSIONS,
    )
    WorkerScanService(
        processor=processor,
        poll_interval_seconds=settings.poll_interval_seconds,
    ).serve()


if __name__ == "__main__":
    run()
