from abc import ABC, abstractmethod
import logging
import time
from typing import Any, TypedDict

from pipeline_common.contracts import doc_id_from_source_key, utc_now_iso
from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway
from parsing.registry import ParserRegistry

logger = logging.getLogger(__name__)


class SecurityConfig(TypedDict):
    """Security-related parse metadata configuration."""

    clearance: str


class DocumentProcessingConfig(TypedDict):
    """Runtime config for parse worker queues, storage, polling, and metadata."""

    poll_interval_seconds: int
    queue: "QueueConfig"
    storage: "StorageConfig"
    security: SecurityConfig


class StorageConfig(TypedDict):
    """Storage-related prefixes and bucket for parse worker."""

    bucket: str
    raw_prefix: str
    processed_prefix: str


class QueueConfig(TypedDict):
    """Queue contract and timeout settings for parse worker."""

    stage: str
    stage_queues: dict[str, Any]
    queue_pop_timeout_seconds: int


class WorkerService(ABC):
    """Minimal worker interface for long-running service loops."""

    @abstractmethod
    def serve(self) -> None:
        """Run the worker loop indefinitely."""


class WorkerParseDocumentService(WorkerService):
    """Transform raw source documents into processed payloads."""

    def __init__(
        self,
        *,
        stage_queue: StageQueue,
        object_storage: ObjectStorageGateway,
        processing_config: DocumentProcessingConfig,
        parser_registry: ParserRegistry,
    ) -> None:
        """Initialize parse worker dependencies and runtime settings."""
        self.stage_queue = stage_queue
        self.object_storage = object_storage
        self.parser_registry = parser_registry
        self._initialize_runtime_config(processing_config)

    def serve(self) -> None:
        """Run the parse worker loop by polling queue messages."""
        while True:
            source_key = self._pop_queued_source_key()
            if source_key is not None:
                try:
                    self.process_source_key(source_key)
                except Exception:
                    logger.exception("Failed processing source key '%s'", source_key)
            time.sleep(self.poll_interval_seconds)

    def process_source_key(self, source_key: str) -> None:
        """Parse a single raw document key and publish downstream work."""
        if not source_key.startswith(self.raw_prefix) or source_key == self.raw_prefix:
            return

        doc_id = doc_id_from_source_key(source_key)
        destination_key = self._processed_key(doc_id)
        if self._processed_exists(destination_key):
            self.stage_queue.push_dlq_message(
                storage_key=source_key,
                doc_id=doc_id,
                error=f"Processed document already exists: {destination_key}",
                failed_at=utc_now_iso(),
            )
            return

        try:
            payload = self._build_processed_payload(source_key, doc_id)
        except Exception as exc:
            self.stage_queue.push_dlq_message(
                storage_key=source_key,
                doc_id=doc_id,
                error=str(exc),
                failed_at=utc_now_iso(),
            )
            logger.exception("Failed parsing source key '%s'; sent to DLQ", source_key)
            return
        self._write_processed_document(destination_key, payload)
        self._enqueue_chunking(destination_key)
        logger.info("Wrote processed document '%s'", destination_key)

    def _pop_queued_source_key(self) -> str | None:
        """Pop one source key from parse queue when available."""
        message = self.stage_queue.pop_message()
        if message and isinstance(message.get("storage_key"), str):
            return str(message["storage_key"])
        return None

    def _processed_key(self, doc_id: str) -> str:
        """Build the processed-stage key for a document id."""
        return f"{self.processed_prefix}{doc_id}.json"

    def _processed_exists(self, destination_key: str) -> bool:
        """Return whether the processed output already exists."""
        return self.object_storage.object_exists(self.storage_bucket, destination_key)

    def _build_processed_payload(self, source_key: str, doc_id: str) -> dict[str, Any]:
        """Parse a source document and map it into fixed + parser payload fields."""
        parser = self.parser_registry.resolve(source_key)
        raw_document = self.object_storage.read_object(self.storage_bucket, source_key)
        parsed_payload = parser.parse(raw_document.decode("utf-8", errors="ignore"))
        return {
            "doc_id": doc_id,
            "source_key": source_key,
            "timestamp": utc_now_iso(),
            "security_clearance": self.security_clearance,
            "parsed": parsed_payload,
        }

    def _write_processed_document(self, destination_key: str, payload: dict[str, Any]) -> None:
        """Persist parsed document payload into the processed S3 stage."""
        self.object_storage.write_json(self.storage_bucket, destination_key, payload)

    def _enqueue_chunking(self, destination_key: str) -> None:
        """Publish chunking work for a newly produced processed document."""
        self.stage_queue.push_produce_message(storage_key=destination_key)

    def _initialize_runtime_config(self, processing_config: DocumentProcessingConfig) -> None:
        self.poll_interval_seconds = processing_config["poll_interval_seconds"]
        self.storage_bucket = processing_config["storage"]["bucket"]
        self.raw_prefix = processing_config["storage"]["raw_prefix"]
        self.processed_prefix = processing_config["storage"]["processed_prefix"]
        self.security_clearance = processing_config["security"]["clearance"]
