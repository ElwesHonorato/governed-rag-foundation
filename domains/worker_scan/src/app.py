from pipeline_common.queue import StageQueue
from pipeline_common.s3 import S3Store, build_s3_client
from configs.constants import HTML_EXTENSIONS, INCOMING_PREFIX, PARSE_QUEUE, RAW_PREFIX
from configs.configs import WorkerS3QueueLoopSettings
from services.scan_cycle_processor import S3ScanCycleProcessor
from services.worker_scan_service import WorkerScanService


def run() -> None:
    settings = WorkerS3QueueLoopSettings.from_env()
    stage_queue = StageQueue(settings.redis_url)
    s3 = S3Store(
        build_s3_client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )
    s3.ensure_workspace(settings.s3_bucket)
    processor = S3ScanCycleProcessor(
        s3=s3,
        stage_queue=stage_queue,
        bucket=settings.s3_bucket,
        incoming_prefix=INCOMING_PREFIX,
        raw_prefix=RAW_PREFIX,
        parse_queue=PARSE_QUEUE,
        extensions=HTML_EXTENSIONS,
    )
    WorkerScanService(
        processor=processor,
        poll_interval_seconds=settings.poll_interval_seconds,
    ).run_forever()


if __name__ == "__main__":
    run()
