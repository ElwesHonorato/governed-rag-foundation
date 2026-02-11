
from abc import ABC, abstractmethod
import hashlib
import json
import logging
import time
from typing import Any, TypedDict

from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway

logger = logging.getLogger(__name__)


class WorkerService(ABC):
    """Minimal worker interface for long-running service loops."""

    @abstractmethod
    def serve(self) -> None:
        """Run the worker loop indefinitely."""


class StorageConfig(TypedDict):
    """Storage-related prefixes and bucket for embedding worker."""

    bucket: str
    chunks_prefix: str
    embeddings_prefix: str


class QueueConfig(TypedDict):
    """Queue contract and timeout settings for embedding worker."""

    stage: str
    stage_queues: dict[str, Any]
    queue_pop_timeout_seconds: int


class EmbedChunksProcessingConfig(TypedDict):
    """Runtime config for embedding worker queues, storage, and polling."""

    poll_interval_seconds: int
    queue: QueueConfig
    storage: StorageConfig


class WorkerEmbedChunksService(WorkerService):
    """Transform chunk artifacts into embedding payloads."""

    def __init__(
        self,
        *,
        stage_queue: StageQueue,
        object_storage: ObjectStorageGateway,
        processing_config: EmbedChunksProcessingConfig,
        dimension: int,
    ) -> None:
        """Initialize embedding worker dependencies and runtime settings."""
        self.stage_queue = stage_queue
        self.object_storage = object_storage
        self._initialize_runtime_config(processing_config)
        self.dimension = dimension

    def serve(self) -> None:
        """Run the embedding worker loop by polling queue messages."""
        while True:
            source_key = self._pop_queued_source_key()
            if source_key is not None:
                try:
                    self.process_source_key(source_key)
                except Exception:
                    self.stage_queue.push_dlq_message(storage_key=source_key)
                    logger.exception("Failed embedding source key '%s'; sent to DLQ", source_key)
            time.sleep(self.poll_interval_seconds)

    def deterministic_embedding(self, text: str) -> list[float]:
        """Generate deterministic pseudo-embedding values for text."""
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        for index in range(self.dimension):
            byte = digest[index % len(digest)]
            values.append((byte / 255.0) * 2.0 - 1.0)
        return values

    def process_source_key(self, source_key: str) -> None:
        """Embed one chunks artifact and publish downstream indexing work."""
        if not source_key.startswith(self.chunks_prefix) or source_key == self.chunks_prefix:
            return
        if not source_key.endswith(self.chunks_suffix):
            return

        payload = self._read_chunks_object(source_key)
        doc_id = str(payload["doc_id"])
        destination_key = self._embeddings_key(doc_id)
        if self._embeddings_exists(destination_key):
            self.stage_queue.push_dlq_message(storage_key=source_key)
            return

        embeddings = self._process_object(payload)
        self._write_embeddings_object(destination_key, {"doc_id": doc_id, "embeddings": embeddings})
        self._enqueue_embeddings_object(destination_key, doc_id)
        logger.info("Wrote embeddings '%s'", destination_key)

    def _pop_queued_source_key(self) -> str | None:
        """Pop one chunks key from embedding queue when available."""
        message = self.stage_queue.pop_message()
        if message is None:
            return None
        return str(message["storage_key"])

    def _embeddings_key(self, doc_id: str) -> str:
        """Build the embeddings-stage key for a document id."""
        return f"{self.embeddings_prefix}{doc_id}.embeddings.json"

    def _embeddings_exists(self, destination_key: str) -> bool:
        """Return whether the embeddings output already exists."""
        return self.object_storage.object_exists(self.storage_bucket, destination_key)

    def _read_chunks_object(self, source_key: str) -> dict[str, Any]:
        """Read and decode the chunks-stage payload."""
        raw_payload = self.object_storage.read_object(self.storage_bucket, source_key)
        return dict(json.loads(raw_payload.decode("utf-8", errors="ignore")))

    def _process_object(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Map each chunk into an embedding record with retained metadata."""
        records: list[dict[str, Any]] = []
        for chunk in payload.get("chunks", []):
            text = str(chunk["chunk_text"])
            records.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "vector": self.deterministic_embedding(text),
                    "metadata": {
                        "source_type": chunk.get("source_type"),
                        "timestamp": chunk.get("timestamp"),
                        "security_clearance": chunk.get("security_clearance"),
                        "doc_id": chunk.get("doc_id"),
                        "source_key": chunk.get("source_key"),
                        "chunk_index": chunk.get("chunk_index"),
                        "chunk_text": text,
                    },
                }
            )
        return records

    def _write_embeddings_object(self, destination_key: str, payload: dict[str, Any]) -> None:
        """Persist embedding payload into the embeddings S3 stage."""
        self.object_storage.write_object(
            self.storage_bucket,
            destination_key,
            json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            content_type="application/json",
        )

    def _enqueue_embeddings_object(self, destination_key: str, doc_id: str) -> None:
        """Publish indexing work for a newly produced embeddings artifact."""
        self.stage_queue.push_produce_message(embeddings_key=destination_key, doc_id=doc_id)

    def _initialize_runtime_config(self, processing_config: EmbedChunksProcessingConfig) -> None:
        """Load runtime config values into worker state."""
        self.poll_interval_seconds = processing_config["poll_interval_seconds"]
        self.storage_bucket = processing_config["storage"]["bucket"]
        self.chunks_prefix = processing_config["storage"]["chunks_prefix"]
        self.embeddings_prefix = processing_config["storage"]["embeddings_prefix"]
        self.chunks_suffix = ".chunks.json"
