
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
    bucket: str


class ManifestProcessingConfig(TypedDict):
    poll_interval_seconds: int
    storage: StorageConfig


class WorkerManifestService(WorkerService):
    def __init__(
        self,
        *,
        storage: ObjectStorageGateway,
        processing_config: ManifestProcessingConfig,
    ) -> None:
        self.storage = storage
        self._initialize_runtime_config(processing_config)

    def serve(self) -> None:
        while True:
            processed_keys = [
                key
                for key in self.storage.list_keys(self.storage_bucket, "03_processed/")
                if key != "03_processed/" and key.endswith(".json")
            ]

            for processed_key in processed_keys:
                doc_id = processed_key.split("/")[-1].replace(".json", "")
                manifest_key = f"07_metadata/manifest/{doc_id}.json"

                status = {
                    "doc_id": doc_id,
                    "stages": {
                        "parse_document": self.storage.object_exists(self.storage_bucket, f"03_processed/{doc_id}.json"),
                        "chunk_text": self.storage.object_exists(self.storage_bucket, f"04_chunks/{doc_id}.chunks.json"),
                        "embed_chunks": self.storage.object_exists(self.storage_bucket, f"05_embeddings/{doc_id}.embeddings.json"),
                        "index_weaviate": self.storage.object_exists(self.storage_bucket, f"06_indexes/{doc_id}.indexed.json"),
                    },
                    "attempts": 1,
                    "last_error": None,
                }
                self.storage.write_object(
                    self.storage_bucket,
                    manifest_key,
                    json.dumps(status, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
                    content_type="application/json",
                )

            time.sleep(self.poll_interval_seconds)

    def _initialize_runtime_config(self, processing_config: ManifestProcessingConfig) -> None:
        self.poll_interval_seconds = processing_config["poll_interval_seconds"]
        self.storage_bucket = processing_config["storage"]["bucket"]
