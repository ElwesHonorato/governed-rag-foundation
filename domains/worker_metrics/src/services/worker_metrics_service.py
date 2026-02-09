from __future__ import annotations

import time

from pipeline_common.observability import Counters
from pipeline_common.s3 import S3Store, build_s3_client
from configs.configs import WorkerS3LoopSettings


class WorkerMetricsService:
    def __init__(self, *, settings: WorkerS3LoopSettings, counters: Counters, s3: S3Store) -> None:
        self.settings = settings
        self.counters = counters
        self.s3 = s3

    @classmethod
    def from_env(cls) -> "WorkerMetricsService":
        settings = WorkerS3LoopSettings.from_env()
        counters = Counters().for_worker("worker_metrics")
        s3 = S3Store(
            build_s3_client(
                endpoint_url=settings.s3_endpoint,
                access_key=settings.s3_access_key,
                secret_key=settings.s3_secret_key,
                region_name=settings.aws_region,
            )
        )
        return cls(settings=settings, counters=counters, s3=s3)

    @staticmethod
    def _count_suffix(keys: list[str], suffix: str) -> int:
        return sum(1 for key in keys if key.endswith(suffix))

    def run_forever(self) -> None:
        while True:
            processed = self.s3.list_keys(self.settings.s3_bucket, "03_processed/")
            chunks = self.s3.list_keys(self.settings.s3_bucket, "04_chunks/")
            embeddings = self.s3.list_keys(self.settings.s3_bucket, "05_embeddings/")
            indexed = self.s3.list_keys(self.settings.s3_bucket, "06_indexes/")

            self.counters.files_processed = self._count_suffix(processed, ".json")
            self.counters.chunks_created = self._count_suffix(chunks, ".chunks.json")
            self.counters.embedding_artifacts = self._count_suffix(embeddings, ".embeddings.json")
            self.counters.index_upserts = self._count_suffix(indexed, ".indexed.json")
            self.counters.emit()
            time.sleep(self.settings.poll_interval_seconds)
