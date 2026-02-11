
from abc import ABC, abstractmethod
import time

from pipeline_common.observability import Counters
from pipeline_common.object_storage import ObjectStorageGateway


class WorkerService(ABC):
    @abstractmethod
    def serve(self) -> None:
        """Run the worker loop indefinitely."""


class WorkerMetricsService(WorkerService):
    def __init__(
        self,
        *,
        counters: Counters,
        storage: ObjectStorageGateway,
        storage_bucket: str,
        poll_interval_seconds: int,
    ) -> None:
        self.counters = counters
        self.storage = storage
        self.storage_bucket = storage_bucket
        self.poll_interval_seconds = poll_interval_seconds

    @staticmethod
    def _count_suffix(keys: list[str], suffix: str) -> int:
        return sum(1 for key in keys if key.endswith(suffix))

    def serve(self) -> None:
        while True:
            processed = self.storage.list_keys(self.storage_bucket, "03_processed/")
            chunks = self.storage.list_keys(self.storage_bucket, "04_chunks/")
            embeddings = self.storage.list_keys(self.storage_bucket, "05_embeddings/")
            indexed = self.storage.list_keys(self.storage_bucket, "06_indexes/")

            self.counters.files_processed = self._count_suffix(processed, ".json")
            self.counters.chunks_created = self._count_suffix(chunks, ".chunks.json")
            self.counters.embedding_artifacts = self._count_suffix(embeddings, ".embeddings.json")
            self.counters.index_upserts = self._count_suffix(indexed, ".indexed.json")
            self.counters.emit()
            time.sleep(self.poll_interval_seconds)
