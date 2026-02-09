
import json
from typing import Any

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


class S3Store:
    def __init__(self, s3_client) -> None:
        self.client = s3_client

    def bucket_exists(self, bucket: str) -> bool:
        try:
            self.client.head_bucket(Bucket=bucket)
            return True
        except Exception:
            return False

    def ensure_workspace(self, bucket: str) -> None:
        if not self.bucket_exists(bucket):
            self.client.create_bucket(Bucket=bucket)
        for prefix in FOLDERS:
            if not self.object_exists(bucket, prefix):
                self.client.put_object(Bucket=bucket, Key=prefix, Body=b"")

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

    def read_text(self, bucket: str, key: str) -> str:
        response = self.client.get_object(Bucket=bucket, Key=key)
        body = response["Body"].read()
        return body.decode("utf-8", errors="ignore")

    def read_json(self, bucket: str, key: str) -> dict[str, Any]:
        return json.loads(self.read_text(bucket, key))

    def write_text(self, bucket: str, key: str, content: str, content_type: str = "text/plain") -> None:
        self.client.put_object(
            Bucket=bucket,
            Key=key,
            Body=content.encode("utf-8"),
            ContentType=content_type,
        )

    def write_json(self, bucket: str, key: str, payload: dict[str, Any]) -> None:
        self.write_text(
            bucket,
            key,
            json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")),
            content_type="application/json",
        )

    def copy(self, bucket: str, source_key: str, destination_key: str) -> None:
        self.client.copy_object(
            Bucket=bucket,
            CopySource={"Bucket": bucket, "Key": source_key},
            Key=destination_key,
        )

    def delete(self, bucket: str, key: str) -> None:
        self.client.delete_object(Bucket=bucket, Key=key)


def build_s3_client(*, endpoint_url: str, access_key: str, secret_key: str, region_name: str):
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region_name,
    )
