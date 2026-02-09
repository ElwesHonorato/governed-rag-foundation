from __future__ import annotations

import time

from pipeline_common.config import Settings
from pipeline_common.observability import Counters
from pipeline_common.s3 import S3Store, build_s3_client


def _count_suffix(keys: list[str], suffix: str) -> int:
    return sum(1 for key in keys if key.endswith(suffix))


def run() -> None:
    settings = Settings()
    counters = Counters().for_worker("worker_metrics")
    s3 = S3Store(
        build_s3_client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )

    while True:
        processed = s3.list_keys(settings.s3_bucket, "03_processed/")
        chunks = s3.list_keys(settings.s3_bucket, "04_chunks/")
        embeddings = s3.list_keys(settings.s3_bucket, "05_embeddings/")
        indexed = s3.list_keys(settings.s3_bucket, "06_indexes/")

        counters.files_processed = _count_suffix(processed, ".json")
        counters.chunks_created = _count_suffix(chunks, ".chunks.json")
        counters.embedding_artifacts = _count_suffix(embeddings, ".embeddings.json")
        counters.index_upserts = _count_suffix(indexed, ".indexed.json")
        counters.emit()
        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    run()
