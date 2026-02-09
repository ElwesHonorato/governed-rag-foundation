from __future__ import annotations

import time

from pipeline_common.observability import Counters
from pipeline_common.s3 import S3Store


class WorkerMetricsService:
    def __init__(
        self,
        *,
        counters: Counters,
        s3: S3Store,
        s3_bucket: str,
        poll_interval_seconds: int,
    ) -> None:
        self.counters = counters
        self.s3 = s3
        self.s3_bucket = s3_bucket
        self.poll_interval_seconds = poll_interval_seconds

    @staticmethod
    def _count_suffix(keys: list[str], suffix: str) -> int:
        return sum(1 for key in keys if key.endswith(suffix))

    def run_forever(self) -> None:
        while True:
            processed = self.s3.list_keys(self.s3_bucket, "03_processed/")
            chunks = self.s3.list_keys(self.s3_bucket, "04_chunks/")
            embeddings = self.s3.list_keys(self.s3_bucket, "05_embeddings/")
            indexed = self.s3.list_keys(self.s3_bucket, "06_indexes/")

            self.counters.files_processed = self._count_suffix(processed, ".json")
            self.counters.chunks_created = self._count_suffix(chunks, ".chunks.json")
            self.counters.embedding_artifacts = self._count_suffix(embeddings, ".embeddings.json")
            self.counters.index_upserts = self._count_suffix(indexed, ".indexed.json")
            self.counters.emit()
            time.sleep(self.poll_interval_seconds)
