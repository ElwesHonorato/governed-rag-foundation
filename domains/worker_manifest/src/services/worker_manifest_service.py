
from abc import ABC, abstractmethod
import time

from pipeline_common.s3 import ObjectStorageGateway


class WorkerService(ABC):
    @abstractmethod
    def serve(self) -> None:
        """Run the worker loop indefinitely."""


class WorkerManifestService(WorkerService):
    def __init__(self, *, s3: ObjectStorageGateway, s3_bucket: str, poll_interval_seconds: int) -> None:
        self.s3 = s3
        self.s3_bucket = s3_bucket
        self.poll_interval_seconds = poll_interval_seconds

    def serve(self) -> None:
        while True:
            processed_keys = [
                key
                for key in self.s3.list_keys(self.s3_bucket, "03_processed/")
                if key != "03_processed/" and key.endswith(".json")
            ]

            for processed_key in processed_keys:
                doc_id = processed_key.split("/")[-1].replace(".json", "")
                manifest_key = f"07_metadata/manifest/{doc_id}.json"

                status = {
                    "doc_id": doc_id,
                    "stages": {
                        "parse_document": self.s3.object_exists(self.s3_bucket, f"03_processed/{doc_id}.json"),
                        "chunk_text": self.s3.object_exists(self.s3_bucket, f"04_chunks/{doc_id}.chunks.json"),
                        "embed_chunks": self.s3.object_exists(self.s3_bucket, f"05_embeddings/{doc_id}.embeddings.json"),
                        "index_weaviate": self.s3.object_exists(self.s3_bucket, f"06_indexes/{doc_id}.indexed.json"),
                    },
                    "attempts": 1,
                    "last_error": None,
                }
                self.s3.write_json(self.s3_bucket, manifest_key, status)

            time.sleep(self.poll_interval_seconds)
