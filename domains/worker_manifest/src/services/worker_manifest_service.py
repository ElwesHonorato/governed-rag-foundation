
from abc import ABC, abstractmethod
import json
import time
from typing import TypedDict

from pipeline_common.object_storage import ObjectStorageGateway


class WorkerService(ABC):
    @abstractmethod
    def serve(self) -> None:
        """Run the worker loop indefinitely."""


class StorageConfig(TypedDict):
    """Storage-related prefixes and bucket for manifest worker."""

    bucket: str
    processed_prefix: str
    chunks_prefix: str
    embeddings_prefix: str
    indexes_prefix: str
    manifest_prefix: str


class ManifestProcessingConfig(TypedDict):
    """Runtime config for manifest worker storage and polling."""

    poll_interval_seconds: int
    storage: StorageConfig


class WorkerManifestService(WorkerService):
    def __init__(
        self,
        *,
        object_storage: ObjectStorageGateway,
        processing_config: ManifestProcessingConfig,
    ) -> None:
        self.object_storage = object_storage
        self._initialize_runtime_config(processing_config)

    def serve(self) -> None:
        while True:
            processed_keys = [
                key
                for key in self.object_storage.list_keys(self.storage_bucket, self.processed_prefix)
                if key != self.processed_prefix and key.endswith(".json")
            ]

            for processed_key in processed_keys:
                doc_id = processed_key.split("/")[-1].replace(".json", "")
                manifest_key = f"{self.manifest_prefix}{doc_id}.json"

                status = {
                    "doc_id": doc_id,
                    "stages": {
                        "parse_document": self.object_storage.object_exists(
                            self.storage_bucket, f"{self.processed_prefix}{doc_id}.json"
                        ),
                        "chunk_text": self.object_storage.object_exists(
                            self.storage_bucket, f"{self.chunks_prefix}{doc_id}.chunks.json"
                        ),
                        "embed_chunks": self.object_storage.object_exists(
                            self.storage_bucket, f"{self.embeddings_prefix}{doc_id}.embeddings.json"
                        ),
                        "index_weaviate": self.object_storage.object_exists(
                            self.storage_bucket, f"{self.indexes_prefix}{doc_id}.indexed.json"
                        ),
                    },
                    "attempts": 1,
                    "last_error": None,
                }
                self.object_storage.write_object(
                    self.storage_bucket,
                    manifest_key,
                    json.dumps(status, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
                    content_type="application/json",
                )

            time.sleep(self.poll_interval_seconds)

    def _initialize_runtime_config(self, processing_config: ManifestProcessingConfig) -> None:
        self.poll_interval_seconds = processing_config["poll_interval_seconds"]
        self.storage_bucket = processing_config["storage"]["bucket"]
        self.processed_prefix = processing_config["storage"]["processed_prefix"]
        self.chunks_prefix = processing_config["storage"]["chunks_prefix"]
        self.embeddings_prefix = processing_config["storage"]["embeddings_prefix"]
        self.indexes_prefix = processing_config["storage"]["indexes_prefix"]
        self.manifest_prefix = processing_config["storage"]["manifest_prefix"]
