from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from configs.constants import HTML_EXTENSIONS, INCOMING_PREFIX, PARSE_QUEUE, RAW_PREFIX, S3_BUCKET
from configs.configs import WorkerS3QueueLoopSettings
from services.scan_cycle_processor import S3ScanCycleProcessor
from services.worker_scan_service import WorkerScanService


def run() -> None:
    settings = WorkerS3QueueLoopSettings.from_env()
    stage_queue = StageQueue(settings.broker_url)
    s3 = ObjectStorageGateway(
        S3Client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )
    s3.bootstrap_bucket_prefixes(S3_BUCKET)
    processor = S3ScanCycleProcessor(
        s3=s3,
        stage_queue=stage_queue,
        bucket=S3_BUCKET,
        source_prefix=INCOMING_PREFIX,
        destination_prefix=RAW_PREFIX,
        parse_queue=PARSE_QUEUE,
        extensions=HTML_EXTENSIONS,
    )
    WorkerScanService(
        processor=processor,
        poll_interval_seconds=settings.poll_interval_seconds,
    ).serve()


if __name__ == "__main__":
    run()
