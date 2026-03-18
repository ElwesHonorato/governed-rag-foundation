"""Index worker orchestration contracts, artifacts, and writers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from pipeline_common.gateways.object_storage import ObjectStorageGateway


@dataclass(frozen=True)
class IndexWorkItem:
    """One indexing work item derived from an inbound URI."""

    uri: str


@dataclass(frozen=True)
class IndexStatusArtifact:
    """Canonical persisted status artifact for one successful index write."""

    doc_id: str
    status: str
    chunk_id: str = ""

    @property
    def to_dict(self) -> dict[str, str]:
        """Serialize one index status artifact for storage persistence."""
        payload = asdict(self)
        if not self.chunk_id:
            payload.pop("chunk_id")
        return payload


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

    def write(self, *, destination_key: str, payload: IndexStatusArtifact) -> None:
        """Write one index status payload to object storage."""
        self._object_storage.write_object(
            uri=self.output_uri(destination_key),
            payload=json.dumps(payload.to_dict, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode(
                "utf-8"
            ),
            content_type="application/json",
        )

    def output_uri(self, destination_key: str) -> str:
        """Build the storage URI for a written index status payload."""
        return self._object_storage.build_uri(self._storage_bucket, destination_key)
