
from abc import ABC, abstractmethod
import json
import time
from typing import TypedDict

from pipeline_common.queue import StageQueue
from pipeline_common.queue.contracts import IndexWeaviateRequested
from pipeline_common.object_storage import ObjectStorageGateway
from pipeline_common.weaviate import upsert_chunk, verify_query


class WorkerService(ABC):
    @abstractmethod
    def serve(self) -> None:
        """Run the worker loop indefinitely."""


class StorageConfig(TypedDict):
    bucket: str


class IndexWeaviateProcessingConfig(TypedDict):
    poll_interval_seconds: int
    storage: StorageConfig


class WorkerIndexWeaviateService(WorkerService):
    def __init__(
        self,
        *,
        stage_queue: StageQueue,
        storage: ObjectStorageGateway,
        processing_config: IndexWeaviateProcessingConfig,
        weaviate_url: str,
    ) -> None:
        self.stage_queue = stage_queue
        self.storage = storage
        self.weaviate_url = weaviate_url
        self._initialize_runtime_config(processing_config)

    def process_source_key(self, source_key: str) -> None:
        if not source_key.startswith("05_embeddings/"):
            return
        if not source_key.endswith(".embeddings.json"):
            return

        payload = json.loads(self.storage.read_object(self.storage_bucket, source_key).decode("utf-8", errors="ignore"))
        for item in payload.get("embeddings", []):
            metadata = dict(item.get("metadata", {}))
            chunk_id = str(item["chunk_id"])
            vector = item.get("vector", [])
            upsert_chunk(
                self.weaviate_url,
                chunk_id=chunk_id,
                vector=vector,
                properties={
                    "chunk_id": chunk_id,
                    "doc_id": metadata.get("doc_id"),
                    "chunk_text": metadata.get("chunk_text"),
                    "source_key": metadata.get("source_key"),
                    "security_clearance": metadata.get("security_clearance"),
                },
            )

        doc_id = payload.get("doc_id", "unknown")
        self.storage.write_object(
            self.storage_bucket,
            f"06_indexes/{doc_id}.indexed.json",
            json.dumps(
                {"doc_id": doc_id, "status": "indexed"},
                sort_keys=True,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("utf-8"),
            content_type="application/json",
        )
        result = verify_query(self.weaviate_url, "logistics")
        print(f"[worker_index_weaviate] indexed doc_id={doc_id} verify={bool(result)}", flush=True)

    def serve(self) -> None:
        while True:
            queued = self.stage_queue.pop()
            if (
                queued
                and isinstance(queued.get("embeddings_key"), str)
                and isinstance(queued.get("doc_id"), str)
            ):
                message = IndexWeaviateRequested(
                    embeddings_key=str(queued["embeddings_key"]),
                    doc_id=str(queued["doc_id"]),
                )
                self.process_source_key(message["embeddings_key"])
            else:
                keys = [
                    key
                    for key in self.storage.list_keys(self.storage_bucket, "05_embeddings/")
                    if key != "05_embeddings/" and key.endswith(".embeddings.json")
                ]
                for source_key in keys:
                    self.process_source_key(source_key)

            time.sleep(self.poll_interval_seconds)

    def _initialize_runtime_config(self, processing_config: IndexWeaviateProcessingConfig) -> None:
        self.poll_interval_seconds = processing_config["poll_interval_seconds"]
        self.storage_bucket = processing_config["storage"]["bucket"]
