from abc import ABC, abstractmethod
from collections.abc import Sequence

from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway


class ScanCycleProcessor(ABC):
    @abstractmethod
    def scan(self) -> int:
        """Run one scan cycle and return the number of processed items."""


class StorageScanCycleProcessor(ScanCycleProcessor):
    """Move objects from a source prefix to a destination prefix and enqueue jobs."""

    def __init__(
        self,
        *,
        storage: ObjectStorageGateway,
        stage_queue: StageQueue,
        bucket: str,
        source_prefix: str,
        destination_prefix: str,
        parse_queue: str,
        extensions: Sequence[str],
    ) -> None:
        self.storage = storage
        self.stage_queue = stage_queue
        self.bucket = bucket
        self.source_prefix = source_prefix
        self.destination_prefix = destination_prefix
        self.parse_queue = parse_queue
        self.extensions = self._normalize_extensions(extensions)

    def scan(self) -> int:
        """Run one scan cycle and return the number of newly moved files."""
        processed = 0
        for source_key in self._candidate_keys():
            processed += int(self._process_source_key(source_key))
        return processed

    def _candidate_keys(self) -> list[str]:
        """List source keys that match the configured extension filter."""
        return [
            key
            for key in self.storage.list_keys(self.bucket, self.source_prefix)
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
        """Check whether the source object is still present."""
        return self.storage.object_exists(self.bucket, source_key)

    def _destination_exists(self, destination_key: str) -> bool:
        """Check whether the destination object already exists."""
        return self.storage.object_exists(self.bucket, destination_key)

    def _copy_and_enqueue(self, source_key: str, destination_key: str) -> None:
        """Copy source object to raw prefix and enqueue downstream parsing."""
        self._copy_source_to_destination(source_key, destination_key)
        self._enqueue_destination(destination_key)
        print(f"[worker_scan] moved {source_key} -> {destination_key}", flush=True)

    def _delete_source(self, source_key: str) -> None:
        """Delete the source object after processing to avoid reprocessing."""
        self.storage.delete(self.bucket, source_key)

    def _copy_source_to_destination(self, source_key: str, destination_key: str) -> None:
        """Copy one source object into the destination path."""
        self.storage.copy(self.bucket, source_key, destination_key)

    def _enqueue_destination(self, destination_key: str) -> None:
        """Enqueue the destination object for downstream parsing."""
        self.stage_queue.push(self.parse_queue, {"raw_key": destination_key})

    def _is_candidate_key(self, key: str) -> bool:
        """Return True when a key is a processable source object."""
        return (
            key.startswith(self.source_prefix)
            and key != self.source_prefix
            and key.endswith(self.extensions)
        )

    def _destination_key(self, source_key: str) -> str:
        """Map a source key to its destination key."""
        return source_key.replace(self.source_prefix, self.destination_prefix, 1)

    def _normalize_extensions(self, extensions: Sequence[str]) -> tuple[str, ...]:
        """Normalize extension list into a tuple for str.endswith checks."""
        return tuple(extensions)
