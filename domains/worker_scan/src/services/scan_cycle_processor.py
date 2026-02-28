from abc import ABC, abstractmethod
from dataclasses import dataclass

import logging

from pipeline_common.contracts import doc_id_from_source_key
from pipeline_common.lineage import DatasetPlatform
from pipeline_common.lineage.data_hub import DataHubRunTimeLineage
from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway

logger = logging.getLogger(__name__)


class ScanCycleProcessor(ABC):
    """Contract for one scan cycle execution."""

    @abstractmethod
    def scan(self) -> int:
        """Run one scan cycle and return the number of processed items."""


@dataclass(frozen=True)
class ScanStorageContract:
    """Storage bucket and stage prefix settings for scan worker."""

    bucket: str
    input_prefix: str
    output_prefix: str


class StorageScanCycleProcessor(ScanCycleProcessor):
    """Move objects from a source prefix to a destination prefix and enqueue jobs."""

    def __init__(
        self,
        *,
        object_storage: ObjectStorageGateway,
        stage_queue: StageQueue,
        lineage: DataHubRunTimeLineage,
        storage_contract: ScanStorageContract,
    ) -> None:
        """Initialize instance state and dependencies."""
        self.object_storage = object_storage
        self.stage_queue = stage_queue
        self.lineage = lineage
        self.bucket = storage_contract.bucket
        self.source_prefix = storage_contract.input_prefix
        self.destination_prefix = storage_contract.output_prefix

    def scan(self) -> int:
        """Run one scan cycle and return the number of newly moved files."""
        processed = 0
        for source_key in self._candidate_keys():
            processed += int(self._process_source_key(source_key))
        return processed

    def _candidate_keys(self) -> list[str]:
        """List source keys from the configured source prefix."""
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
        self.lineage.start_run()
        self.lineage.add_input(name=f"{self.bucket}/{source_key}", platform=DatasetPlatform.S3)
        self.lineage.add_output(name=f"{self.bucket}/{destination_key}", platform=DatasetPlatform.S3)
        try:
            self._copy_source_to_destination(source_key, destination_key)
            self.lineage.complete_run()
            self._enqueue_parse_request(destination_key)
            self._delete_source(source_key)
            logger.info(
                "Moved '%s' -> '%s' (source_doc_id=%s, dest_doc_id=%s)",
                source_key,
                destination_key,
                doc_id_from_source_key(source_key),
                doc_id_from_source_key(destination_key),
            )
            return True
        except Exception:
            self.lineage.abort_run()
            raise

    def _source_exists(self, source_key: str) -> bool:
        """Check whether the source object is still present."""
        return self.object_storage.object_exists(self.bucket, source_key)

    def _destination_exists(self, destination_key: str) -> bool:
        """Check whether the destination object already exists."""
        return self.object_storage.object_exists(self.bucket, destination_key)

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
        return key.startswith(self.source_prefix) and key != self.source_prefix

    def _destination_key(self, source_key: str) -> str:
        """Map a source key to its destination key."""
        return source_key.replace(self.source_prefix, self.destination_prefix, 1)
