from abc import ABC, abstractmethod
import logging
import time
from typing import TypedDict

from pipeline_common.contracts import doc_id_from_source_key, utc_now_iso
from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway
from parsing.registry import ParserRegistry

logger = logging.getLogger(__name__)


class SecurityConfig(TypedDict):
    """Security-related parse metadata configuration."""

    clearance: str


class DocumentProcessingConfig(TypedDict):
    """Grouped metadata configuration emitted with processed payloads."""

    poll_interval_seconds: int
    queue: "QueueConfig"
    storage: "StorageConfig"
    security: SecurityConfig


class QueueConfig(TypedDict):
    """Queue names used by parse worker."""

    parse_queue: str
    parse_dlq_queue: str
    chunk_text_queue: str


class StorageConfig(TypedDict):
    """Storage-related prefixes and bucket for parse worker."""

    bucket: str
    raw_prefix: str
    processed_prefix: str


class WorkerService(ABC):
    @abstractmethod
    def serve(self) -> None:
        """Run the worker loop indefinitely."""


class WorkerParseDocumentService(WorkerService):
    """Transform raw source documents into processed payloads."""

    def __init__(
        self,
        *,
        stage_queue: StageQueue,
        storage: ObjectStorageGateway,
        processing_config: DocumentProcessingConfig,
        parser_registry: ParserRegistry,
    ) -> None:
        """Initialize parse worker dependencies and runtime settings."""
        self.stage_queue = stage_queue
        self.storage = storage
        self.processing_config = processing_config
        self.parser_registry = parser_registry

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
        self._enqueue_chunking(destination_key, doc_id)
        logger.info("Wrote processed document '%s'", destination_key)

    def serve(self) -> None:
        """Run the parse worker loop by queue-first then S3-fallback polling."""
        while True:
            for source_key in self._next_source_keys():
                try:
                    self.process_source_key(source_key)
                except Exception:
                    logger.exception("Failed processing source key '%s'", source_key)
            time.sleep(self._poll_interval_seconds())

    def _next_source_keys(self) -> list[str]:
        """Return source keys from queue first, then from S3 polling fallback."""
        queued = self.stage_queue.pop(self._parse_queue_name(), timeout_seconds=1)
        if queued and isinstance(queued.get("raw_key"), str):
            return [str(queued["raw_key"])]
        return [
            key
            for key in self.storage.list_keys(self._storage_bucket(), self._raw_prefix())
            if self._is_supported_source_key(key)
        ]

    def _is_supported_source_key(self, source_key: str) -> bool:
        """Return whether a source key is in the raw stage."""
        raw_prefix = self._raw_prefix()
        return (
            source_key.startswith(raw_prefix)
            and source_key != raw_prefix
        )

    def _processed_key(self, doc_id: str) -> str:
        """Build the processed-stage key for a document id."""
        return f"{self._processed_prefix()}{doc_id}.json"

    def _processed_exists(self, destination_key: str) -> bool:
        """Return whether the processed output already exists."""
        return self.storage.object_exists(self._storage_bucket(), destination_key)

    def _build_processed_payload(self, source_key: str, doc_id: str) -> dict[str, str]:
        """Parse a source document and map it into processed payload fields."""
        parser = self.parser_registry.resolve(source_key)
        parsed_document = parser.parse(self.storage.read_text(self._storage_bucket(), source_key))
        return {
            "doc_id": doc_id,
            "source_key": source_key,
            "timestamp": utc_now_iso(),
            "security_clearance": self.processing_config["security"]["clearance"],
            "title": parsed_document.title,
            "text": parsed_document.text,
        }

    def _write_processed_document(self, destination_key: str, payload: dict[str, str]) -> None:
        """Persist parsed document payload into the processed S3 stage."""
        self.storage.write_json(self._storage_bucket(), destination_key, payload)

    def _enqueue_chunking(self, destination_key: str, doc_id: str) -> None:
        """Publish chunking work for a newly produced processed document."""
        self.stage_queue.push(self._chunk_text_queue_name(), {"processed_key": destination_key, "doc_id": doc_id})

    def _enqueue_parse_dlq(self, source_key: str, doc_id: str, error: str) -> None:
        """Publish parse failures to DLQ for later inspection/retry."""
        self.stage_queue.push(
            self._parse_dlq_queue_name(),
            {
                "raw_key": source_key,
                "doc_id": doc_id,
                "error": error,
                "failed_at": utc_now_iso(),
            },
        )

    def _raw_prefix(self) -> str:
        return self.processing_config["storage"]["raw_prefix"]

    def _processed_prefix(self) -> str:
        return self.processing_config["storage"]["processed_prefix"]

    def _storage_bucket(self) -> str:
        return self.processing_config["storage"]["bucket"]

    def _poll_interval_seconds(self) -> int:
        return self.processing_config["poll_interval_seconds"]

    def _parse_queue_name(self) -> str:
        return self.processing_config["queue"]["parse_queue"]

    def _chunk_text_queue_name(self) -> str:
        return self.processing_config["queue"]["chunk_text_queue"]

    def _parse_dlq_queue_name(self) -> str:
        return self.processing_config["queue"]["parse_dlq_queue"]
