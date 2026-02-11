
from typing import Any, Protocol

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


class ObjectStorageGateway:
    def __init__(self, client: "ObjectStorageClient") -> None:
        self.client = client

    def bucket_exists(self, bucket: str) -> bool:
        return self.client.bucket_exists(bucket)

    def bootstrap_bucket_prefixes(self, bucket: str) -> None:
        if not self.bucket_exists(bucket):
            self.client.create_bucket(bucket)
        for prefix in FOLDERS:
            if not self.object_exists(bucket, prefix):
                self.client.write_bytes(bucket, prefix, b"", content_type="application/octet-stream")

    def object_exists(self, bucket: str, key: str) -> bool:
        return self.client.object_exists(bucket, key)

    def list_keys(self, bucket: str, prefix: str) -> list[str]:
        return self.client.list_keys(bucket, prefix)

    def read_object(self, bucket: str, key: str) -> bytes:
        return self.client.read_bytes(bucket, key)

    def write_object(
        self,
        bucket: str,
        key: str,
        payload: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        self.client.write_bytes(bucket, key, payload, content_type=content_type)

    def copy(self, bucket: str, source_key: str, destination_key: str) -> None:
        self.client.copy_object(bucket, source_key, destination_key)

    def delete(self, bucket: str, key: str) -> None:
        self.client.delete_object(bucket, key)


class ObjectStorageClient(Protocol):
    def bucket_exists(self, bucket: str) -> bool:
        ...

    def create_bucket(self, bucket: str) -> None:
        ...

    def object_exists(self, bucket: str, key: str) -> bool:
        ...

    def list_keys(self, bucket: str, prefix: str) -> list[str]:
        ...

    def read_bytes(self, bucket: str, key: str) -> bytes:
        ...

    def write_bytes(self, bucket: str, key: str, payload: bytes, content_type: str) -> None:
        ...

    def copy_object(self, bucket: str, source_key: str, destination_key: str) -> None:
        ...

    def delete_object(self, bucket: str, key: str) -> None:
        ...


class S3Client:
    def __init__(self, *, endpoint_url: str, access_key: str, secret_key: str, region_name: str) -> None:
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name,
        )

    def bucket_exists(self, bucket: str) -> bool:
        try:
            self.client.head_bucket(Bucket=bucket)
            return True
        except Exception:
            return False

    def create_bucket(self, bucket: str) -> None:
        self.client.create_bucket(Bucket=bucket)

    def object_exists(self, bucket: str, key: str) -> bool:
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False

    def list_keys(self, bucket: str, prefix: str) -> list[str]:
        keys: list[str] = []
        continuation_token: str | None = None
        while True:
            params: dict[str, Any] = {"Bucket": bucket, "Prefix": prefix}
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

    def read_bytes(self, bucket: str, key: str) -> bytes:
        response = self.client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    def write_bytes(self, bucket: str, key: str, payload: bytes, content_type: str) -> None:
        self.client.put_object(
            Bucket=bucket,
            Key=key,
            Body=payload,
            ContentType=content_type,
        )

    def copy_object(self, bucket: str, source_key: str, destination_key: str) -> None:
        self.client.copy_object(
            Bucket=bucket,
            CopySource={"Bucket": bucket, "Key": source_key},
            Key=destination_key,
        )

    def delete_object(self, bucket: str, key: str) -> None:
        self.client.delete_object(Bucket=bucket, Key=key)
