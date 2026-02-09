
from pipeline_common.queue import StageQueue
from pipeline_common.s3 import S3Store


class ScanCycleProcessor:
    def __init__(
        self,
        *,
        s3: S3Store,
        stage_queue: StageQueue,
        bucket: str,
        incoming_prefix: str,
        raw_prefix: str,
        parse_queue: str,
        extension: str,
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
