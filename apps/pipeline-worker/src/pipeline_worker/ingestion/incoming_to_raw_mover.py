from __future__ import annotations

from pipeline_worker.storage.s3_workspace import S3ObjectStore


class IncomingToRawMover:
    def __init__(
        self,
        *,
        store: S3ObjectStore,
        incoming_prefix: str = "01_incoming/",
        raw_prefix: str = "02_raw/",
    ) -> None:
        self.store = store
        self.incoming_prefix = incoming_prefix
        self.raw_prefix = raw_prefix

    def move(self, *, bucket: str, keys: list[str]) -> None:
        for source_key in keys:
            destination_key = self._destination_key(source_key)
            if destination_key is None:
                continue

            if self.store.object_exists(bucket, destination_key):
                if self.store.object_exists(bucket, source_key):
                    self.store.delete_object(bucket, source_key)
                continue

            if not self.store.object_exists(bucket, source_key):
                continue

            self.store.copy_object(bucket, source_key, destination_key)
            self.store.delete_object(bucket, source_key)

    def _destination_key(self, source_key: str) -> str | None:
        if not source_key.startswith(self.incoming_prefix):
            return None
        suffix = source_key[len(self.incoming_prefix) :]
        if not suffix:
            return None
        return f"{self.raw_prefix}{suffix}"
