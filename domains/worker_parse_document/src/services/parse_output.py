"""Parse worker orchestration contracts and writers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import Envelope


@dataclass(frozen=True)
class ParseWorkItem:
    """One parse work item derived from inbound queue payload."""

    input_uri: str
    doc_id: str
    destination_key: str


class ParseOutputWriter:
    """Write processed parse payloads and build downstream messages."""

    def __init__(
        self,
        *,
        object_storage: ObjectStorageGateway,
        storage_bucket: str,
    ) -> None:
        self._object_storage = object_storage
        self._storage_bucket = storage_bucket

    def write(self, *, destination_key: str, payload: dict[str, Any]) -> None:
        """Write one processed parse payload."""
        self._object_storage.write_object(
            uri=self.output_uri(destination_key),
            payload=json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            content_type="application/json",
        )

    def build_output_message(self, *, destination_key: str) -> Envelope:
        """Build the downstream queue message for a written parse payload."""
        return Envelope(payload=self.output_uri(destination_key))

    def output_uri(self, destination_key: str) -> str:
        """Build the storage URI for a written parse payload."""
        return self._object_storage.build_uri(self._storage_bucket, destination_key)
