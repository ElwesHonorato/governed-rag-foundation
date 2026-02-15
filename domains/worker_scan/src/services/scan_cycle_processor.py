from abc import ABC, abstractmethod

from collections.abc import Sequence
import logging
from typing import TypedDict

from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway
from pipeline_common.lineage import LineageEmitter
from pipeline_common.lineage.paths import s3_uri

logger = logging.getLogger(__name__)


class ScanCycleProcessor(ABC):
    """Contract for one scan cycle execution."""

    @abstractmethod
    def scan(self) -> int:
        """Run one scan cycle and return the number of processed items."""


class StorageConfig(TypedDict):
    """Storage bucket and stage prefix settings for scan worker."""
    bucket: str
    incoming_prefix: str
    raw_prefix: str


class FiltersConfig(TypedDict):
    """File-extension filters used to select processable source keys."""
    extensions: list[str]


class ScanProcessingConfig(TypedDict):
    """Runtime config for scan cycle storage and filtering."""
    storage: StorageConfig
    filters: FiltersConfig


class StorageScanCycleProcessor(ScanCycleProcessor):
    """Move objects from a source prefix to a destination prefix and enqueue jobs."""

    def __init__(
        self,
        *,
        object_storage: ObjectStorageGateway,
        stage_queue: StageQueue,
        lineage: LineageEmitter,
        processing_config: ScanProcessingConfig,
    ) -> None:
        """Initialize instance state and dependencies."""
        self.object_storage = object_storage
        self.stage_queue = stage_queue
        self.lineage = lineage
        self._initialize_runtime_config(processing_config)

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
            for key in self.object_storage.list_keys(self.bucket, self.source_prefix)
            if self._is_candidate_key(key)
        ]

    def _process_source_key(self, source_key: str) -> bool:
        """Handle one source key and return whether it was copied/enqueued."""
        if not self._source_exists(source_key):
            return False

        destination_key = self._destination_key(source_key)
        self.lineage.start_run(
            inputs=[s3_uri(self.bucket, source_key)],
            outputs=[s3_uri(self.bucket, destination_key)],
        )
        try:
            self._copy_and_enqueue(source_key, destination_key)
            self._delete_source(source_key)
            self.lineage.complete_run()
            return True
        except Exception as exc:
            self.lineage.fail_run(error_message=str(exc))
            raise

    def _source_exists(self, source_key: str) -> bool:
        """Check whether the source object is still present."""
        return self.object_storage.object_exists(self.bucket, source_key)

    def _destination_exists(self, destination_key: str) -> bool:
        """Check whether the destination object already exists."""
        return self.object_storage.object_exists(self.bucket, destination_key)

    def _copy_and_enqueue(self, source_key: str, destination_key: str) -> None:
        """Copy source object to raw prefix and enqueue downstream parsing."""
        self._copy_source_to_destination(source_key, destination_key)
        self._enqueue_parse_request(destination_key)
        logger.info("Moved '%s' -> '%s'", source_key, destination_key)

    def _delete_source(self, source_key: str) -> None:
        """Delete the source object after processing to avoid reprocessing."""
        self.object_storage.delete(self.bucket, source_key)

    def _copy_source_to_destination(self, source_key: str, destination_key: str) -> None:
        """Copy one source object into the destination path."""
        self.object_storage.copy(self.bucket, source_key, destination_key)

    def _enqueue_parse_request(self, destination_key: str) -> None:
        """Publish parse-stage work for the destination raw object."""
        self.stage_queue.push_produce_message(storage_key=destination_key)

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

    def _initialize_runtime_config(self, processing_config: ScanProcessingConfig) -> None:
        """Internal helper for initialize runtime config."""
        self.bucket = processing_config["storage"]["bucket"]
        self.source_prefix = processing_config["storage"]["incoming_prefix"]
        self.destination_prefix = processing_config["storage"]["raw_prefix"]
        self.extensions = self._normalize_extensions(processing_config["filters"]["extensions"])
