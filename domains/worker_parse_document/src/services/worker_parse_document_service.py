from abc import ABC, abstractmethod
import logging
import time
from typing import TypedDict

from pipeline_common.contracts import doc_id_from_source_key, utc_now_iso
from pipeline_common.queue import StageQueue
from pipeline_common.queue.contracts import ParseDocumentFailed, QueueStorageKeyMessage
from pipeline_common.object_storage import ObjectStorageGateway
from parsing.registry import ParserRegistry

logger = logging.getLogger(__name__)


class SecurityConfig(TypedDict):
    """Security-related parse metadata configuration."""

    clearance: str


class DocumentProcessingConfig(TypedDict):
    """Runtime config for parse worker queues, storage, polling, and metadata."""

    queue_pop_timeout_seconds: int
    storage: "StorageConfig"
    security: SecurityConfig


class StorageConfig(TypedDict):
    """Storage-related prefixes and bucket for parse worker."""

    bucket: str
    raw_prefix: str
    processed_prefix: str


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
        poll_interval_seconds: int,
        processing_config: DocumentProcessingConfig,
        parser_registry: ParserRegistry,
    ) -> None:
        """Initialize parse worker dependencies and runtime settings."""
        self.stage_queue = stage_queue
        self.object_storage = object_storage
        self.poll_interval_seconds = poll_interval_seconds
        self.parser_registry = parser_registry
        self._initialize_runtime_config(processing_config)

    def process_source_key(self, source_key: str) -> None:
        """Parse a single raw document key and publish downstream work."""
        if not self._is_supported_source_key(source_key):
            return

        doc_id = doc_id_from_source_key(source_key)
        destination_key = self._processed_key(doc_id)
        if self._processed_exists(destination_key):
            return

        try:
            payload = self._build_processed_payload(source_key, doc_id)
        except Exception as exc:
            self._enqueue_parse_dlq(source_key, doc_id, str(exc))
            logger.exception("Failed parsing source key '%s'; sent to DLQ", source_key)
            return
        self._write_processed_document(destination_key, payload)
        self._enqueue_chunking(destination_key)
        logger.info("Wrote processed document '%s'", destination_key)

    def serve(self) -> None:
        """Run the parse worker loop by queue-first then S3-fallback polling."""
        while True:
            for source_key in self._next_source_keys():
                try:
                    self.process_source_key(source_key)
                except Exception:
                    logger.exception("Failed processing source key '%s'", source_key)
            time.sleep(self.poll_interval_seconds)

    def _next_source_keys(self) -> list[str]:
        """Return source keys from queue first, then from S3 polling fallback."""
        queued_source_key = self._pop_queued_source_key()
        if queued_source_key is not None:
            return [queued_source_key]
        return self._scan_source_keys()

    def _pop_queued_source_key(self) -> str | None:
        """Pop one source key from parse queue when available."""
        queued = self.stage_queue.pop(timeout_seconds=self.queue_pop_timeout_seconds)
        if queued and isinstance(queued.get("storage_key"), str):
            message = QueueStorageKeyMessage(storage_key=str(queued["storage_key"]))
            return message["storage_key"]
        return None

    def _scan_source_keys(self) -> list[str]:
        """List supported source keys from storage raw prefix."""
        return [
            key
            for key in self.object_storage.list_keys(self.storage_bucket, self.raw_prefix)
            if self._is_supported_source_key(key)
        ]

    def _is_supported_source_key(self, source_key: str) -> bool:
        """Return whether a source key is in the raw stage."""
        return (
            source_key.startswith(self.raw_prefix)
            and source_key != self.raw_prefix
        )

    def _processed_key(self, doc_id: str) -> str:
        """Build the processed-stage key for a document id."""
        return f"{self.processed_prefix}{doc_id}.json"

    def _processed_exists(self, destination_key: str) -> bool:
        """Return whether the processed output already exists."""
        return self.object_storage.object_exists(self.storage_bucket, destination_key)

    def _build_processed_payload(self, source_key: str, doc_id: str) -> dict[str, str]:
        """Parse a source document and map it into processed payload fields."""
        parser = self.parser_registry.resolve(source_key)
        parsed_document = parser.parse(self.object_storage.read_text(self.storage_bucket, source_key))
        return {
            "doc_id": doc_id,
            "source_key": source_key,
            "timestamp": utc_now_iso(),
            "security_clearance": self.security_clearance,
            "title": parsed_document.title,
            "text": parsed_document.text,
        }

    def _write_processed_document(self, destination_key: str, payload: dict[str, str]) -> None:
        """Persist parsed document payload into the processed S3 stage."""
        self.object_storage.write_json(self.storage_bucket, destination_key, payload)

    def _enqueue_chunking(self, destination_key: str) -> None:
        """Publish chunking work for a newly produced processed document."""
        self.stage_queue.push(QueueStorageKeyMessage(storage_key=destination_key))

    def _enqueue_parse_dlq(self, source_key: str, doc_id: str, error: str) -> None:
        """Publish parse failures to DLQ for later inspection/retry."""
        self.stage_queue.push_dlq(
            ParseDocumentFailed(
                storage_key=source_key,
                doc_id=doc_id,
                error=error,
                failed_at=utc_now_iso(),
            ),
        )

    def _initialize_runtime_config(self, processing_config: DocumentProcessingConfig) -> None:
        self.queue_pop_timeout_seconds = processing_config["queue_pop_timeout_seconds"]
        self.storage_bucket = processing_config["storage"]["bucket"]
        self.raw_prefix = processing_config["storage"]["raw_prefix"]
        self.processed_prefix = processing_config["storage"]["processed_prefix"]
        self.security_clearance = processing_config["security"]["clearance"]
