import logging
import time
from typing import TypedDict

from pipeline_common.lineage import DatasetPlatform
from pipeline_common.lineage.data_hub import DataHubRunTimeLineage
from pipeline_common.observability import Counters
from pipeline_common.object_storage import ObjectStorageGateway
from pipeline_common.startup.contracts import WorkerService

logger = logging.getLogger(__name__)


class StorageConfig(TypedDict):
    """Storage-related prefixes and bucket for metrics worker."""

    bucket: str
    processed_prefix: str
    chunks_prefix: str
    embeddings_prefix: str
    indexes_prefix: str


class MetricsProcessingConfig(TypedDict):
    """Runtime config for metrics worker storage and polling."""

    poll_interval_seconds: int
    storage: StorageConfig


class WorkerMetricsService(WorkerService):
    """Emit pipeline stage counters on a fixed interval."""
    def __init__(
        self,
        *,
        counters: Counters,
        object_storage: ObjectStorageGateway,
        lineage: DataHubRunTimeLineage,
        processing_config: MetricsProcessingConfig,
    ) -> None:
        """Initialize instance state and dependencies."""
        self.counters = counters
        self.object_storage = object_storage
        self.lineage = lineage
        self._initialize_runtime_config(processing_config)

    @staticmethod
    def _count_suffix(keys: list[str], suffix: str) -> int:
        """Internal helper for count suffix."""
        return sum(1 for key in keys if key.endswith(suffix))

    @staticmethod
    def _count_suffixes(keys: list[str], suffixes: tuple[str, ...]) -> int:
        """Count keys that end with any suffix from the provided tuple."""
        return sum(1 for key in keys if key.endswith(suffixes))

    def serve(self) -> None:
        """Run the worker loop indefinitely."""
        while True:
            self.lineage.start_run()
            self.lineage.add_input(
                name=f"{self.storage_bucket}/{self.processed_prefix}",
                platform=DatasetPlatform.S3,
            )
            self.lineage.add_input(
                name=f"{self.storage_bucket}/{self.chunks_prefix}",
                platform=DatasetPlatform.S3,
            )
            self.lineage.add_input(
                name=f"{self.storage_bucket}/{self.embeddings_prefix}",
                platform=DatasetPlatform.S3,
            )
            self.lineage.add_input(
                name=f"{self.storage_bucket}/{self.indexes_prefix}",
                platform=DatasetPlatform.S3,
            )
            try:
                processed = self.object_storage.list_keys(self.storage_bucket, self.processed_prefix)
                chunks = self.object_storage.list_keys(self.storage_bucket, self.chunks_prefix)
                embeddings = self.object_storage.list_keys(self.storage_bucket, self.embeddings_prefix)
                indexed = self.object_storage.list_keys(self.storage_bucket, self.indexes_prefix)

                self.counters.files_processed = self._count_suffix(processed, ".json")
                self.counters.chunks_created = self._count_suffixes(chunks, (".chunk.json", ".chunks.json"))
                self.counters.embedding_artifacts = self._count_suffixes(
                    embeddings, (".embedding.json", ".embeddings.json")
                )
                self.counters.index_upserts = self._count_suffix(indexed, ".indexed.json")
                self.counters.emit()
                self.lineage.complete_run()
            except Exception as exc:
                self.lineage.fail_run(error_message=str(exc))
                logger.exception("Failed collecting pipeline metrics")
            time.sleep(self.poll_interval_seconds)

    def _initialize_runtime_config(self, processing_config: MetricsProcessingConfig) -> None:
        """Internal helper for initialize runtime config."""
        self.poll_interval_seconds = processing_config["poll_interval_seconds"]
        self.storage_bucket = processing_config["storage"]["bucket"]
        self.processed_prefix = processing_config["storage"]["processed_prefix"]
        self.chunks_prefix = processing_config["storage"]["chunks_prefix"]
        self.embeddings_prefix = processing_config["storage"]["embeddings_prefix"]
        self.indexes_prefix = processing_config["storage"]["indexes_prefix"]
