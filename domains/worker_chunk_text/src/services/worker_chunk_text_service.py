
from abc import ABC, abstractmethod
import json
import logging
from typing import Any, TypedDict

from pipeline_common.contracts import chunk_id_for
from pipeline_common.lineage import LineageEmitter
from pipeline_common.lineage.paths import s3_uri
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
        lineage: LineageEmitter,
        processing_config: ChunkTextProcessingConfig,
    ) -> None:
        """Initialize chunking worker dependencies and runtime settings."""
        self.stage_queue = stage_queue
        self.object_storage = object_storage
        self.lineage = lineage
        self._initialize_runtime_config(processing_config)

    def serve(self) -> None:
        """Run the chunking worker loop by polling queue messages."""
        while True:
            source_key = self._pop_queued_source_key()
            if source_key is None:
                continue
            try:
                self.process_source_key(source_key)
            except Exception:
                self.stage_queue.push_dlq_message(storage_key=source_key)
                logger.exception("Failed chunking source key '%s'; sent to DLQ", source_key)

    def process_source_key(self, source_key: str) -> None:
        """Chunk one processed document and publish per-chunk downstream work."""
        if not source_key.startswith(self.processed_prefix) or source_key == self.processed_prefix:
            return
        if not source_key.endswith(self.processed_suffix):
            return

        doc_id = source_key.split("/")[-1].replace(self.processed_suffix, "")
        destination_prefix = f"{self.chunks_prefix}{doc_id}/"
        self.lineage.start_run(
            inputs=[s3_uri(self.storage_bucket, source_key)],
            outputs=[s3_uri(self.storage_bucket, destination_prefix)],
        )
        try:
            processed = self._read_processed_object(source_key)
            doc_id = str(processed["doc_id"])
            chunk_records = self._build_chunk_records(processed, doc_id)
            written = 0
            for chunk_record in chunk_records:
                destination_key = self._chunk_object_key(doc_id, str(chunk_record["chunk_id"]))
                if not self._chunk_object_exists(destination_key):
                    self._write_chunk_object(destination_key, chunk_record)
                    written += 1
                self._enqueue_chunk_object(destination_key)
            self.lineage.complete_run(
                inputs=[s3_uri(self.storage_bucket, source_key)],
                outputs=[s3_uri(self.storage_bucket, f"{self.chunks_prefix}{doc_id}/")],
            )
            logger.info("Wrote %d chunk objects for doc_id '%s'", written, doc_id)
        except Exception as exc:
            self.lineage.fail_run(error_message=str(exc))
            raise

    def _pop_queued_source_key(self) -> str | None:
        """Pop one processed object key from chunking queue when available."""
        message = self.stage_queue.pop_message()
        if message is None:
            return None
        return str(message["storage_key"])

    def _chunk_object_key(self, doc_id: str, chunk_id: str) -> str:
        """Build one chunk object key scoped under the document id."""
        return f"{self.chunks_prefix}{doc_id}/{chunk_id}.chunk.json"

    def _chunk_object_exists(self, destination_key: str) -> bool:
        """Return whether one chunk object already exists."""
        return self.object_storage.object_exists(self.storage_bucket, destination_key)

    def _read_processed_object(self, source_key: str) -> dict[str, Any]:
        """Read and decode the processed-stage payload."""
        raw_payload = self.object_storage.read_object(self.storage_bucket, source_key)
        return dict(json.loads(raw_payload.decode("utf-8", errors="ignore")))

    def _build_chunk_records(self, processed: dict[str, Any], doc_id: str) -> list[dict[str, Any]]:
        """Map a processed payload into deterministic per-chunk records."""
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
        return records

    def _write_chunk_object(self, destination_key: str, payload: dict[str, Any]) -> None:
        """Persist one chunk payload into the chunks S3 stage."""
        self.object_storage.write_object(
            self.storage_bucket,
            destination_key,
            json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            content_type="application/json",
        )

    def _enqueue_chunk_object(self, destination_key: str) -> None:
        """Publish embedding work for one chunk object artifact."""
        self.stage_queue.push_produce_message(storage_key=destination_key)

    def _initialize_runtime_config(self, processing_config: ChunkTextProcessingConfig) -> None:
        """Load runtime config values into worker state."""
        self.poll_interval_seconds = processing_config["poll_interval_seconds"]
        self.storage_bucket = processing_config["storage"]["bucket"]
        self.processed_prefix = processing_config["storage"]["processed_prefix"]
        self.chunks_prefix = processing_config["storage"]["chunks_prefix"]
        self.processed_suffix = ".json"
