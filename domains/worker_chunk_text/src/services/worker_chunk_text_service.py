
from abc import ABC, abstractmethod
import json
import logging
import time
from typing import Any, TypedDict

from pipeline_common.contracts import chunk_id_for
from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway
from pipeline_common.text import chunk_text

logger = logging.getLogger(__name__)


class WorkerService(ABC):
    """Minimal worker interface for long-running service loops."""

    @abstractmethod
    def serve(self) -> None:
        """Run the worker loop indefinitely."""


class StorageConfig(TypedDict):
    """Storage-related prefixes and bucket for chunking worker."""

    bucket: str
    processed_prefix: str
    chunks_prefix: str


class QueueConfig(TypedDict):
    """Queue contract and timeout settings for chunking worker."""

    stage: str
    stage_queues: dict[str, Any]
    queue_pop_timeout_seconds: int


class ChunkTextProcessingConfig(TypedDict):
    """Runtime config for chunking worker queues, storage, and polling."""

    poll_interval_seconds: int
    queue: QueueConfig
    storage: StorageConfig


class WorkerChunkTextService(WorkerService):
    """Transform processed document payloads into chunk artifacts."""

    def __init__(
        self,
        *,
        stage_queue: StageQueue,
        object_storage: ObjectStorageGateway,
        processing_config: ChunkTextProcessingConfig,
    ) -> None:
        """Initialize chunking worker dependencies and runtime settings."""
        self.stage_queue = stage_queue
        self.object_storage = object_storage
        self._initialize_runtime_config(processing_config)

    def serve(self) -> None:
        """Run the chunking worker loop by polling queue messages."""
        while True:
            source_key = self._pop_queued_source_key()
            if source_key is not None:
                try:
                    self.process_source_key(source_key)
                except Exception:
                    self.stage_queue.push_dlq_message(storage_key=source_key)
                    logger.exception("Failed chunking source key '%s'; sent to DLQ", source_key)
            time.sleep(self.poll_interval_seconds)

    def process_source_key(self, source_key: str) -> None:
        """Chunk one processed document and publish downstream work."""
        if not source_key.startswith(self.processed_prefix) or source_key == self.processed_prefix:
            return
        if not source_key.endswith(self.processed_suffix):
            return

        processed = self._read_processed_object(source_key)
        doc_id = str(processed["doc_id"])
        destination_key = self._chunks_key(doc_id)
        if self._chunks_exists(destination_key):
            self.stage_queue.push_dlq_message(storage_key=source_key)
            return

        payload = self._process_object(processed, doc_id)
        self._write_chunked_object(destination_key, payload)
        self._enqueue_chunked_object(destination_key)
        logger.info("Wrote chunks '%s'", destination_key)

    def _pop_queued_source_key(self) -> str | None:
        """Pop one processed object key from chunking queue when available."""
        message = self.stage_queue.pop_message()
        if message is None:
            return None
        return str(message["storage_key"])

    def _chunks_key(self, doc_id: str) -> str:
        """Build the chunks-stage key for a document id."""
        return f"{self.chunks_prefix}{doc_id}.chunks.json"

    def _chunks_exists(self, destination_key: str) -> bool:
        """Return whether the chunked output already exists."""
        return self.object_storage.object_exists(self.storage_bucket, destination_key)

    def _read_processed_object(self, source_key: str) -> dict[str, Any]:
        """Read and decode the processed-stage payload."""
        raw_payload = self.object_storage.read_object(self.storage_bucket, source_key)
        return dict(json.loads(raw_payload.decode("utf-8", errors="ignore")))

    def _process_object(self, processed: dict[str, Any], doc_id: str) -> dict[str, Any]:
        """Map a processed payload into deterministic chunk records."""
        parsed_payload = processed.get("parsed")
        parsed_text = parsed_payload.get("text", "") if isinstance(parsed_payload, dict) else ""
        chunks = chunk_text(str(parsed_text or processed.get("text", "")))
        records: list[dict[str, Any]] = []
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
        return {"doc_id": doc_id, "chunks": records}

    def _write_chunked_object(self, destination_key: str, payload: dict[str, Any]) -> None:
        """Persist chunk payload into the chunks S3 stage."""
        self.object_storage.write_object(
            self.storage_bucket,
            destination_key,
            json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            content_type="application/json",
        )

    def _enqueue_chunked_object(self, destination_key: str) -> None:
        """Publish embedding work for a newly produced chunk artifact."""
        self.stage_queue.push_produce_message(storage_key=destination_key)

    def _initialize_runtime_config(self, processing_config: ChunkTextProcessingConfig) -> None:
        """Load runtime config values into worker state."""
        self.poll_interval_seconds = processing_config["poll_interval_seconds"]
        self.storage_bucket = processing_config["storage"]["bucket"]
        self.processed_prefix = processing_config["storage"]["processed_prefix"]
        self.chunks_prefix = processing_config["storage"]["chunks_prefix"]
        self.processed_suffix = ".json"
