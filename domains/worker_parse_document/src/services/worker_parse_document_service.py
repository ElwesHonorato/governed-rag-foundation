from abc import ABC, abstractmethod
import logging
import time
from typing import TypedDict

from pipeline_common.contracts import doc_id_from_source_key, utc_now_iso
from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway
from parsing.registry import ParserRegistry

logger = logging.getLogger(__name__)


class SourceConfig(TypedDict):
    """Source-related parse metadata configuration."""

    type: str


class SecurityConfig(TypedDict):
    """Security-related parse metadata configuration."""

    clearance: str


class DocumentProcessingConfig(TypedDict):
    """Grouped metadata configuration emitted with processed payloads."""

    source: SourceConfig
    security: SecurityConfig


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
        storage_bucket: str,
        poll_interval_seconds: int,
        processing_config: DocumentProcessingConfig,
        parser_registry: ParserRegistry,
    ) -> None:
        """Initialize parse worker dependencies and runtime settings."""
        self.stage_queue = stage_queue
        self.storage = storage
        self.storage_bucket = storage_bucket
        self.poll_interval_seconds = poll_interval_seconds
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

        payload = self._build_processed_payload(source_key, doc_id)
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
            time.sleep(self.poll_interval_seconds)

    def _next_source_keys(self) -> list[str]:
        """Return source keys from queue first, then from S3 polling fallback."""
        queued = self.stage_queue.pop("q.parse_document", timeout_seconds=1)
        if queued and isinstance(queued.get("raw_key"), str):
            return [str(queued["raw_key"])]
        return [
            key
            for key in self.storage.list_keys(self.storage_bucket, "02_raw/")
            if self._is_supported_source_key(key)
        ]

    def _is_supported_source_key(self, source_key: str) -> bool:
        """Return whether a source key is in the raw stage and has a known parser."""
        return (
            source_key.startswith("02_raw/")
            and source_key != "02_raw/"
            and self.parser_registry.can_resolve(source_key)
        )

    def _processed_key(self, doc_id: str) -> str:
        """Build the processed-stage key for a document id."""
        return f"03_processed/{doc_id}.json"

    def _processed_exists(self, destination_key: str) -> bool:
        """Return whether the processed output already exists."""
        return self.storage.object_exists(self.storage_bucket, destination_key)

    def _build_processed_payload(self, source_key: str, doc_id: str) -> dict[str, str]:
        """Parse a source document and map it into processed payload fields."""
        parser = self.parser_registry.resolve(source_key)
        parsed_document = parser.parse(self.storage.read_text(self.storage_bucket, source_key))
        return {
            "doc_id": doc_id,
            "source_key": source_key,
            "source_type": self.processing_config["source"]["type"],
            "timestamp": utc_now_iso(),
            "security_clearance": self.processing_config["security"]["clearance"],
            "title": parsed_document.title,
            "text": parsed_document.text,
        }

    def _write_processed_document(self, destination_key: str, payload: dict[str, str]) -> None:
        """Persist parsed document payload into the processed S3 stage."""
        self.storage.write_json(self.storage_bucket, destination_key, payload)

    def _enqueue_chunking(self, destination_key: str, doc_id: str) -> None:
        """Publish chunking work for a newly produced processed document."""
        self.stage_queue.push("q.chunk_text", {"processed_key": destination_key, "doc_id": doc_id})
