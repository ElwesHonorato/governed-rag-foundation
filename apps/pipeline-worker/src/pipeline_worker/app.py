from __future__ import annotations

import time

from pipeline_worker.config import Settings
from pipeline_worker.ingestion.incoming_scanner import IncomingFileScanner
from pipeline_worker.ingestion.incoming_to_raw_mover import IncomingToRawMover
from pipeline_worker.storage.s3_workspace import (
    FOLDERS,
    S3ObjectStore,
    WorkspaceBootstrap,
    build_s3_client,
)


def poll_incoming_files(*, scanner: IncomingFileScanner, bucket: str) -> list[str]:
    return scanner.scan(bucket)


def process_pending_files(*, mover: IncomingToRawMover, bucket: str, keys: list[str]) -> None:
    mover.move(bucket=bucket, keys=keys)


def run() -> None:
    settings = Settings()
    s3_client = build_s3_client(
        endpoint_url=settings.s3_endpoint,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        region_name=settings.aws_region,
    )
    store = S3ObjectStore(s3_client)
    scanner = IncomingFileScanner(store=store)
    mover = IncomingToRawMover(store=store)
    bootstrap = WorkspaceBootstrap(
        bucket=settings.s3_bucket,
        folders=FOLDERS,
        store=store,
    )
    bootstrap.bootstrap()

    while True:
        pending_files = poll_incoming_files(scanner=scanner, bucket=settings.s3_bucket)
        if pending_files:
            process_pending_files(mover=mover, bucket=settings.s3_bucket, keys=pending_files)
        time.sleep(30)


if __name__ == "__main__":
    run()
