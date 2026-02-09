from collections.abc import Sequence

from pipeline_common.queue import StageQueue
from pipeline_common.s3 import S3Store
from services.cycle_processor import CycleProcessor


class ScanCycleProcessor(CycleProcessor):
    """Move incoming S3 objects to raw storage and enqueue parse jobs."""

    def __init__(
        self,
        *,
        s3: S3Store,
        stage_queue: StageQueue,
        bucket: str,
        incoming_prefix: str,
        raw_prefix: str,
        parse_queue: str,
        extensions: Sequence[str],
    ) -> None:
        self.s3 = s3
        self.stage_queue = stage_queue
        self.bucket = bucket
        self.incoming_prefix = incoming_prefix
        self.raw_prefix = raw_prefix
        self.parse_queue = parse_queue
        self.extensions = self._normalize_extensions(extensions)

    def scan(self) -> int:
        """Run one scan cycle and return the number of newly moved files."""
        processed = 0
        for source_key in self._candidate_keys():
            processed += int(self._process_source_key(source_key))
        return processed

    def _candidate_keys(self) -> list[str]:
        """List incoming keys that match the configured extension filter."""
        return [
            key
            for key in self.s3.list_keys(self.bucket, self.incoming_prefix)
            if self._is_candidate_key(key)
        ]

    def _process_source_key(self, source_key: str) -> bool:
        """Handle one source key and return whether it was copied/enqueued."""
        if not self._source_exists(source_key):
            return False

        destination_key = self._destination_key(source_key)
        moved = False
        if not self._destination_exists(destination_key):
            self._copy_and_enqueue(source_key, destination_key)
            moved = True

        self._delete_source(source_key)
        return moved

    def _source_exists(self, source_key: str) -> bool:
        """Check whether the source object is still present in S3."""
        return self.s3.object_exists(self.bucket, source_key)

    def _destination_exists(self, destination_key: str) -> bool:
        """Check whether the destination object already exists in S3."""
        return self.s3.object_exists(self.bucket, destination_key)

    def _copy_and_enqueue(self, source_key: str, destination_key: str) -> None:
        """Copy source object to raw prefix and enqueue downstream parsing."""
        self.s3.copy(self.bucket, source_key, destination_key)
        self.stage_queue.push(self.parse_queue, {"raw_key": destination_key})
        print(f"[worker_scan] moved {source_key} -> {destination_key}", flush=True)

    def _delete_source(self, source_key: str) -> None:
        """Delete the source object after processing to avoid reprocessing."""
        self.s3.delete(self.bucket, source_key)

    def _is_candidate_key(self, key: str) -> bool:
        """Return True when a key is a processable incoming file."""
        return (
            key.startswith(self.incoming_prefix)
            and key != self.incoming_prefix
            and key.endswith(self.extensions)
        )

    def _destination_key(self, source_key: str) -> str:
        """Map an incoming key to its destination raw key."""
        return source_key.replace(self.incoming_prefix, self.raw_prefix, 1)

    def _normalize_extensions(self, extensions: Sequence[str]) -> tuple[str, ...]:
        """Normalize extension list into a tuple for str.endswith checks."""
        return tuple(extensions)
