from __future__ import annotations

import time

from pipeline_common.queue import StageQueue
from pipeline_common.s3 import S3Store, build_s3_client
from configs.configs import WorkerS3QueueLoopSettings


class ScanCycleProcessor:
    INCOMING_PREFIX = "01_incoming/"
    RAW_PREFIX = "02_raw/"
    PARSE_QUEUE = "q.parse_document"
    HTML_EXTENSION = ".html"

    def __init__(
        self,
        *,
        s3: S3Store,
        stage_queue: StageQueue,
        bucket: str,
        incoming_prefix: str = INCOMING_PREFIX,
        raw_prefix: str = RAW_PREFIX,
        parse_queue: str = PARSE_QUEUE,
        extension: str = HTML_EXTENSION,
    ) -> None:
        self.s3 = s3
        self.stage_queue = stage_queue
        self.bucket = bucket
        self.incoming_prefix = incoming_prefix
        self.raw_prefix = raw_prefix
        self.parse_queue = parse_queue
        self.extension = extension

    def process_once(self) -> int:
        processed = 0
        keys = [
            key
            for key in self.s3.list_keys(self.bucket, self.incoming_prefix)
            if self._is_candidate_key(key)
        ]
        for source_key in keys:
            destination_key = self._destination_key(source_key)
            if not self.s3.object_exists(self.bucket, source_key):
                continue
            if not self.s3.object_exists(self.bucket, destination_key):
                self.s3.copy(self.bucket, source_key, destination_key)
                self.stage_queue.push(self.parse_queue, {"raw_key": destination_key})
                print(f"[worker_scan] moved {source_key} -> {destination_key}", flush=True)
                processed += 1
            self.s3.delete(self.bucket, source_key)
        return processed

    def _is_candidate_key(self, key: str) -> bool:
        return (
            key.startswith(self.incoming_prefix)
            and key != self.incoming_prefix
            and key.endswith(self.extension)
        )

    def _destination_key(self, source_key: str) -> str:
        return source_key.replace(self.incoming_prefix, self.raw_prefix, 1)


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


def run() -> None:
    WorkerScanService.from_env().run_forever()


if __name__ == "__main__":
    run()
