from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from configs.constants import SCAN_PROCESSING_CONFIG
from configs.configs import WorkerS3QueueLoopSettings
from services.scan_cycle_processor import StorageScanCycleProcessor
from services.worker_scan_service import WorkerScanService


def run() -> None:
    settings = WorkerS3QueueLoopSettings.from_env()
    processing_config = SCAN_PROCESSING_CONFIG
    stage_queue = StageQueue(settings.broker_url, queue_config=processing_config["queue"])
    storage = ObjectStorageGateway(
        S3Client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )
    storage.bootstrap_bucket_prefixes(processing_config["storage"]["bucket"])
    processor = StorageScanCycleProcessor(
        storage=storage,
        stage_queue=stage_queue,
        bucket=processing_config["storage"]["bucket"],
        source_prefix=processing_config["storage"]["incoming_prefix"],
        destination_prefix=processing_config["storage"]["raw_prefix"],
        extensions=processing_config["filters"]["extensions"],
    )
    WorkerScanService(
        processor=processor,
        poll_interval_seconds=settings.poll_interval_seconds,
    ).serve()


if __name__ == "__main__":
    run()
