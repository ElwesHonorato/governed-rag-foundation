from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.settings import QueueRuntimeSettings, S3StorageSettings
from configs.constants import SCAN_PROCESSING_CONFIG
from services.scan_cycle_processor import StorageScanCycleProcessor
from services.worker_scan_service import WorkerScanService


def run() -> None:
    s3_settings = S3StorageSettings.from_env()
    queue_settings = QueueRuntimeSettings.from_env()
    processing_config = SCAN_PROCESSING_CONFIG
    stage_queue = StageQueue(queue_settings.broker_url, queue_config=processing_config["queue"])
    object_storage = ObjectStorageGateway(
        S3Client(
            endpoint_url=s3_settings.s3_endpoint,
            access_key=s3_settings.s3_access_key,
            secret_key=s3_settings.s3_secret_key,
            region_name=s3_settings.aws_region,
        )
    )
    object_storage.bootstrap_bucket_prefixes(processing_config["storage"]["bucket"])
    processor = StorageScanCycleProcessor(
        storage=object_storage,
        stage_queue=stage_queue,
        processing_config=processing_config,
    )
    WorkerScanService(
        processor=processor,
        processing_config=processing_config,
    ).serve()


if __name__ == "__main__":
    run()
