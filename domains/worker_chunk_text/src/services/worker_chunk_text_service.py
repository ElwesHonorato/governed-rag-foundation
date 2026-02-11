
from abc import ABC, abstractmethod
import time
from typing import TypedDict

from pipeline_common.contracts import chunk_id_for
from pipeline_common.queue import StageQueue
from pipeline_common.queue.contracts import QueueStorageKeyMessage
from pipeline_common.object_storage import ObjectStorageGateway
from pipeline_common.text import chunk_text


class WorkerService(ABC):
    @abstractmethod
    def serve(self) -> None:
        """Run the worker loop indefinitely."""


class StorageConfig(TypedDict):
    bucket: str


class ChunkTextProcessingConfig(TypedDict):
    poll_interval_seconds: int
    storage: StorageConfig


class WorkerChunkTextService(WorkerService):
    def __init__(
        self,
        *,
        stage_queue: StageQueue,
        storage: ObjectStorageGateway,
        processing_config: ChunkTextProcessingConfig,
    ) -> None:
        self.stage_queue = stage_queue
        self.storage = storage
        self._initialize_runtime_config(processing_config)

    def process_source_key(self, source_key: str) -> None:
        if not source_key.startswith("03_processed/"):
            return
        if not source_key.endswith(".json"):
            return

        processed = self.storage.read_json(self.storage_bucket, source_key)
        doc_id = str(processed["doc_id"])
        destination_key = f"04_chunks/{doc_id}.chunks.json"
        if self.storage.object_exists(self.storage_bucket, destination_key):
            return

        chunks = chunk_text(str(processed.get("text", "")))
        records = []
        for index, chunk in enumerate(chunks):
            records.append(
                {
                    "chunk_id": chunk_id_for(doc_id, index, chunk),
                    "doc_id": doc_id,
                    "chunk_index": index,
                    "chunk_text": chunk,
                    "source_type": processed.get("source_type", "html"),
                    "timestamp": processed.get("timestamp"),
                    "security_clearance": processed.get("security_clearance", "internal"),
                    "source_key": processed.get("source_key"),
                }
            )

        self.storage.write_json(self.storage_bucket, destination_key, {"doc_id": doc_id, "chunks": records})
        self.stage_queue.push(QueueStorageKeyMessage(storage_key=destination_key))
        print(f"[worker_chunk_text] wrote {destination_key} chunks={len(records)}", flush=True)

    def serve(self) -> None:
        while True:
            queued = self.stage_queue.pop()
            if queued and isinstance(queued.get("storage_key"), str):
                message = QueueStorageKeyMessage(storage_key=str(queued["storage_key"]))
                self.process_source_key(message["storage_key"])
            else:
                keys = [
                    key
                    for key in self.storage.list_keys(self.storage_bucket, "03_processed/")
                    if key != "03_processed/" and key.endswith(".json")
                ]
                for source_key in keys:
                    self.process_source_key(source_key)

            time.sleep(self.poll_interval_seconds)

    def _initialize_runtime_config(self, processing_config: ChunkTextProcessingConfig) -> None:
        self.poll_interval_seconds = processing_config["poll_interval_seconds"]
        self.storage_bucket = processing_config["storage"]["bucket"]
