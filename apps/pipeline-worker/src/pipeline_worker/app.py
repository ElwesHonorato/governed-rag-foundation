from __future__ import annotations

import time

from pipeline_worker.config import Settings
from pipeline_worker.storage.s3_workspace import (
    FOLDERS,
    S3ObjectStore,
    WorkspaceBootstrap,
    build_s3_client,
)


def run() -> None:
    settings = Settings()
    s3_client = build_s3_client(
        endpoint_url=settings.s3_endpoint,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        region_name=settings.aws_region,
    )
    store = S3ObjectStore(s3_client)
    bootstrap = WorkspaceBootstrap(
        bucket=settings.s3_bucket,
        folders=FOLDERS,
        store=store,
    )
    bootstrap.bootstrap()

    while True:
        time.sleep(30)


if __name__ == "__main__":
    run()
