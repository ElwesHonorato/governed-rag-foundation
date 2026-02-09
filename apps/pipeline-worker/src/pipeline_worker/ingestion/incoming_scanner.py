from __future__ import annotations

from pipeline_worker.storage.s3_workspace import S3ObjectStore


class IncomingFileScanner:
    def __init__(self, *, store: S3ObjectStore, incoming_prefix: str = "01_incoming/") -> None:
        self.store = store
        self.incoming_prefix = incoming_prefix

    def scan(self, bucket: str) -> list[str]:
        keys = self.store.list_object_keys(bucket=bucket, prefix=self.incoming_prefix)
        return [key for key in keys if key != self.incoming_prefix and not key.endswith("/")]
