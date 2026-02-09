from __future__ import annotations

import boto3

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
    def __init__(self, *, bucket: str, folders: tuple[str, ...], store: "S3ObjectStore") -> None:
        self.bucket = bucket
        self.folders = folders
        self.store = store

    def bootstrap(self) -> str:
        self.ensure_bucket(self.bucket)
        self.ensure_prefixes(self.bucket, self.folders)
        return self.bucket

    def ensure_bucket(self, bucket: str) -> None:
        if self.bucket_exists(bucket):
            return
        self.store.create_bucket(bucket)

    def ensure_prefixes(self, bucket: str, prefixes: tuple[str, ...]) -> None:
        for prefix in prefixes:
            key = prefix if prefix.endswith("/") else f"{prefix}/"
            if self.object_exists(bucket, key):
                continue
            self.store.create_empty_object(bucket, key)

    def bucket_exists(self, bucket: str) -> bool:
        return self.store.bucket_exists(bucket)

    def object_exists(self, bucket: str, key: str) -> bool:
        return self.store.object_exists(bucket, key)


class S3ObjectStore:
    def __init__(self, s3_client) -> None:
        self.client = s3_client

    def bucket_exists(self, bucket: str) -> bool:
        try:
            self.client.head_bucket(Bucket=bucket)
            return True
        except Exception:
            return False

    def object_exists(self, bucket: str, key: str) -> bool:
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False

    def create_bucket(self, bucket: str) -> None:
        self.client.create_bucket(Bucket=bucket)

    def create_empty_object(self, bucket: str, key: str) -> None:
        self.client.put_object(Bucket=bucket, Key=key, Body=b"")

    def list_object_keys(self, bucket: str, prefix: str) -> list[str]:
        keys: list[str] = []
        continuation_token: str | None = None

        while True:
            params = {"Bucket": bucket, "Prefix": prefix}
            if continuation_token:
                params["ContinuationToken"] = continuation_token

            response = self.client.list_objects_v2(**params)
            for item in response.get("Contents", []):
                key = item.get("Key")
                if isinstance(key, str):
                    keys.append(key)

            if not response.get("IsTruncated"):
                break
            continuation_token = response.get("NextContinuationToken")

        return keys

    def copy_object(self, bucket: str, source_key: str, destination_key: str) -> None:
        self.client.copy_object(
            Bucket=bucket,
            CopySource={"Bucket": bucket, "Key": source_key},
            Key=destination_key,
        )

    def delete_object(self, bucket: str, key: str) -> None:
        self.client.delete_object(Bucket=bucket, Key=key)

def build_s3_client(*, endpoint_url: str, access_key: str, secret_key: str, region_name: str):
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region_name,
    )
