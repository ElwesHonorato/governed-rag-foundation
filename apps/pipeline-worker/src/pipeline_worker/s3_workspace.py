from __future__ import annotations

import boto3
from botocore.exceptions import ClientError

from pipeline_worker.config import Settings

FOLDERS = (
    "01_incoming/",
    "02_raw/",
    "03_processed/",
    "04_chunks/",
    "05_embeddings/",
    "06_indexes/",
    "07_metadata/",
    "08_evals/",
    "09_tmp/",
)


class WorkspaceBootstrap:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )

    def bootstrap(self) -> str:
        self._ensure_bucket(self.settings.s3_bucket)
        self._ensure_folders(self.settings.s3_bucket)
        return self.settings.s3_bucket

    def _ensure_bucket(self, bucket: str) -> None:
        if self._bucket_exists(bucket):
            return
        self.client.create_bucket(Bucket=bucket)

    def _bucket_exists(self, bucket: str) -> bool:
        try:
            self.client.head_bucket(Bucket=bucket)
            return True
        except ClientError:
            return False

    def _ensure_folders(self, bucket: str) -> None:
        for folder in FOLDERS:
            if self._object_exists(bucket, folder):
                continue
            self.client.put_object(Bucket=bucket, Key=folder, Body=b"")

    def _object_exists(self, bucket: str, key: str) -> bool:
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False
