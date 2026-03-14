"""Index worker orchestration contracts and writers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from pipeline_common.gateways.object_storage import ObjectStorageGateway


@dataclass(frozen=True)
class IndexWorkItem:
    """One indexing work item derived from an inbound URI."""

    uri: str


class IndexStatusWriter:
    """Write index status artifacts for successful Weaviate upserts."""

    def __init__(
        self,
        *,
        object_storage: ObjectStorageGateway,
        storage_bucket: str,
    ) -> None:
        self._object_storage = object_storage
        self._storage_bucket = storage_bucket

    def write(self, *, destination_key: str, payload: dict[str, Any]) -> None:
        """Write one index status payload to object storage."""
        self._object_storage.write_object(
            uri=self.output_uri(destination_key),
            payload=json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            content_type="application/json",
        )

    def output_uri(self, destination_key: str) -> str:
        """Build the storage URI for a written index status payload."""
        return self._object_storage.build_uri(self._storage_bucket, destination_key)
