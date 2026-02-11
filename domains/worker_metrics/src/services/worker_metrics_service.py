
from abc import ABC, abstractmethod
import time
from typing import TypedDict

from pipeline_common.observability import Counters
from pipeline_common.object_storage import ObjectStorageGateway


class WorkerService(ABC):
    @abstractmethod
    def serve(self) -> None:
        """Run the worker loop indefinitely."""


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
    def __init__(
        self,
        *,
        counters: Counters,
        object_storage: ObjectStorageGateway,
        processing_config: MetricsProcessingConfig,
    ) -> None:
        self.counters = counters
        self.object_storage = object_storage
        self._initialize_runtime_config(processing_config)

    @staticmethod
    def _count_suffix(keys: list[str], suffix: str) -> int:
        return sum(1 for key in keys if key.endswith(suffix))

    def serve(self) -> None:
        while True:
            processed = self.object_storage.list_keys(self.storage_bucket, self.processed_prefix)
            chunks = self.object_storage.list_keys(self.storage_bucket, self.chunks_prefix)
            embeddings = self.object_storage.list_keys(self.storage_bucket, self.embeddings_prefix)
            indexed = self.object_storage.list_keys(self.storage_bucket, self.indexes_prefix)

            self.counters.files_processed = self._count_suffix(processed, ".json")
            self.counters.chunks_created = self._count_suffix(chunks, ".chunks.json")
            self.counters.embedding_artifacts = self._count_suffix(embeddings, ".embeddings.json")
            self.counters.index_upserts = self._count_suffix(indexed, ".indexed.json")
            self.counters.emit()
            time.sleep(self.poll_interval_seconds)

    def _initialize_runtime_config(self, processing_config: MetricsProcessingConfig) -> None:
        self.poll_interval_seconds = processing_config["poll_interval_seconds"]
        self.storage_bucket = processing_config["storage"]["bucket"]
        self.processed_prefix = processing_config["storage"]["processed_prefix"]
        self.chunks_prefix = processing_config["storage"]["chunks_prefix"]
        self.embeddings_prefix = processing_config["storage"]["embeddings_prefix"]
        self.indexes_prefix = processing_config["storage"]["indexes_prefix"]
