
from abc import ABC, abstractmethod
import time

from pipeline_common.object_storage import ObjectStorageGateway


class WorkerService(ABC):
    @abstractmethod
    def serve(self) -> None:
        """Run the worker loop indefinitely."""


class WorkerManifestService(WorkerService):
    def __init__(self, *, storage: ObjectStorageGateway, storage_bucket: str, poll_interval_seconds: int) -> None:
        self.storage = storage
        self.storage_bucket = storage_bucket
        self.poll_interval_seconds = poll_interval_seconds

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
                self.storage.write_json(self.storage_bucket, manifest_key, status)

            time.sleep(self.poll_interval_seconds)
