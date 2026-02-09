from __future__ import annotations

import time

from pipeline_common.queue import StageQueue
from pipeline_common.s3 import S3Store, build_s3_client
from configs.configs import WorkerS3QueueLoopSettings

from services.scan_cycle_processor import ScanCycleProcessor


class WorkerScanService:
    def __init__(
        self,
        *,
        settings: WorkerS3QueueLoopSettings,
        processor: ScanCycleProcessor,
        s3: S3Store,
    ) -> None:
        self.settings = settings
        self.processor = processor
        self.s3 = s3

    @classmethod
    def from_env(cls) -> "WorkerScanService":
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
        processor = ScanCycleProcessor(s3=s3, stage_queue=stage_queue, bucket=settings.s3_bucket)
        return cls(settings=settings, processor=processor, s3=s3)

    def run_forever(self) -> None:
        while True:
            self.processor.process_once()
            time.sleep(self.settings.poll_interval_seconds)
