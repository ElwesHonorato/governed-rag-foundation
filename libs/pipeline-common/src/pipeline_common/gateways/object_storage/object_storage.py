
"""Object storage infrastructure adapters.

Layer:
- Infrastructure adapter used by worker services.

Role:
- Expose a stable object-storage API while delegating driver specifics to a
  client implementation (for example S3-compatible boto3 client).

Design intent:
- Keep storage driver details out of worker business logic.

Non-goals:
- This module does not implement domain validation for payload schemas.
"""

from typing import Any, ClassVar, Protocol

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
    """Facade over an object-storage client implementation.

    Layer:
    - Infrastructure adapter facade.

    Dependencies:
    - An ``ObjectStorageClient`` implementation.

    Design intent:
    - Provide worker-facing storage operations independent of client library.

    Non-goals:
    - No retry/backoff policy abstraction beyond client call behavior.
    """
    def __init__(self, client: "ObjectStorageClient") -> None:
        """Initialize instance state and dependencies."""
        self.client = client

    def bucket_exists(self, bucket: str) -> bool:
        """Execute bucket exists."""
        return self.client.bucket_exists(bucket)

    def bootstrap_bucket_prefixes(self, bucket: str) -> None:
        """Execute bootstrap bucket prefixes."""
        if not self.bucket_exists(bucket):
            self.client.create_bucket(bucket)
        for prefix in FOLDERS:
            if not self.object_exists(bucket, prefix):
                self.client.write_bytes(bucket, prefix, b"", content_type="application/octet-stream")

    def object_exists(self, bucket: str, key: str) -> bool:
        """Execute object exists."""
        return self.client.object_exists(bucket, key)

    def list_keys(self, bucket: str, prefix: str) -> list[str]:
        """Execute list keys."""
        return self.client.list_keys(bucket, prefix)

    def build_uri(self, bucket: str, key: str) -> str:
        """Build a storage URI from bucket and key parts."""
        return f"{self.client.URI_SCHEME}://{bucket}/{key}"

    def read_object(self, uri: str) -> bytes:
        """Execute read object from an ``s3a://`` URI."""
        bucket, key = self._split_source_uri(uri)
        return self.client.read_bytes(bucket, key)

    def write_object(
        self,
        uri: str,
        payload: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        """Execute write object."""
        bucket, key = self._split_source_uri(uri)
        self.client.write_bytes(bucket, key, payload, content_type=content_type)

    def copy(self, bucket: str, source_key: str, destination_key: str) -> None:
        """Execute copy."""
        self.client.copy_object(bucket, source_key, destination_key)

    def delete(self, bucket: str, key: str) -> None:
        """Execute delete."""
        self.client.delete_object(bucket, key)

    def _split_source_uri(self, source_uri: str) -> tuple[str, str]:
        uri_without_scheme = source_uri.split("://", 1)[-1]
        bucket, key = uri_without_scheme.split("/", 1)
        return bucket, key


class ObjectStorageClient(Protocol):
    """Port contract implemented by concrete object-storage clients."""

    URI_SCHEME: ClassVar[str]

    def bucket_exists(self, bucket: str) -> bool:
        """Execute bucket exists."""
        ...

    def create_bucket(self, bucket: str) -> None:
        """Execute create bucket."""
        ...

    def object_exists(self, bucket: str, key: str) -> bool:
        """Execute object exists."""
        ...

    def list_keys(self, bucket: str, prefix: str) -> list[str]:
        """Execute list keys."""
        ...

    def read_bytes(self, bucket: str, key: str) -> bytes:
        """Execute read bytes."""
        ...

    def write_bytes(self, bucket: str, key: str, payload: bytes, content_type: str) -> None:
        """Execute write bytes."""
        ...

    def copy_object(self, bucket: str, source_key: str, destination_key: str) -> None:
        """Execute copy object."""
        ...

    def delete_object(self, bucket: str, key: str) -> None:
        """Execute delete object."""
        ...


class S3Client:
    """Concrete S3-compatible client adapter backed by boto3.

    Layer:
    - Infrastructure adapter implementation.

    Dependencies:
    - boto3 S3 client.

    Design intent:
    - Implement ``ObjectStorageClient`` using a widely available S3 API.

    Non-goals:
    - This class does not expose boto3 objects to worker code.
    """

    URI_SCHEME: ClassVar[str] = "s3a"

    def __init__(self, *, endpoint_url: str, access_key: str, secret_key: str, region_name: str) -> None:
        """Initialize instance state and dependencies."""
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name,
        )

    def bucket_exists(self, bucket: str) -> bool:
        """Execute bucket exists."""
        try:
            self.client.head_bucket(Bucket=bucket)
            return True
        except Exception:
            return False

    def create_bucket(self, bucket: str) -> None:
        """Execute create bucket."""
        self.client.create_bucket(Bucket=bucket)

    def object_exists(self, bucket: str, key: str) -> bool:
        """Execute object exists."""
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False

    def list_keys(self, bucket: str, prefix: str) -> list[str]:
        """Execute list keys."""
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
        """Execute read bytes."""
        response = self.client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    def write_bytes(self, bucket: str, key: str, payload: bytes, content_type: str) -> None:
        """Execute write bytes."""
        self.client.put_object(
            Bucket=bucket,
            Key=key,
            Body=payload,
            ContentType=content_type,
        )

    def copy_object(self, bucket: str, source_key: str, destination_key: str) -> None:
        """Execute copy object."""
        self.client.copy_object(
            Bucket=bucket,
            CopySource={"Bucket": bucket, "Key": source_key},
            Key=destination_key,
        )

    def delete_object(self, bucket: str, key: str) -> None:
        """Execute delete object."""
        self.client.delete_object(Bucket=bucket, Key=key)
