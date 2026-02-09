from __future__ import annotations

import time

from pipeline_common.config import WorkerS3QueueLoopSettings
from pipeline_common.queue import StageQueue
from pipeline_common.s3 import S3Store, build_s3_client


def run() -> None:
    settings = WorkerS3QueueLoopSettings.from_env()
    stage_queue = StageQueue(settings.redis_url)
    s3 = S3Store(
        build_s3_client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )
    s3.ensure_workspace(settings.s3_bucket)

    while True:
        keys = [
            key
            for key in s3.list_keys(settings.s3_bucket, "01_incoming/")
            if key.startswith("01_incoming/") and key != "01_incoming/" and key.endswith(".html")
        ]
        for source_key in keys:
            destination_key = source_key.replace("01_incoming/", "02_raw/", 1)
            if not s3.object_exists(settings.s3_bucket, source_key):
                continue
            if not s3.object_exists(settings.s3_bucket, destination_key):
                s3.copy(settings.s3_bucket, source_key, destination_key)
                stage_queue.push("q.parse_document", {"raw_key": destination_key})
                print(f"[worker_scan] moved {source_key} -> {destination_key}", flush=True)
            s3.delete(settings.s3_bucket, source_key)

        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    run()
