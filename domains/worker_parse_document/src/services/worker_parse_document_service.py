from abc import ABC, abstractmethod

import json
import logging
from typing import Any, TypedDict

from pipeline_common.contracts import doc_id_from_source_key, utc_now_iso
from pipeline_common.lineage import LineageEmitter
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
        lineage: LineageEmitter,
        processing_config: DocumentProcessingConfig,
        parser_registry: ParserRegistry,
    ) -> None:
        """Initialize parse worker dependencies and runtime settings."""
        self.stage_queue = stage_queue
        self.object_storage = object_storage
        self.lineage = lineage
        self.parser_registry = parser_registry
        self._initialize_runtime_config(processing_config)

    def serve(self) -> None:
        """Run the parse worker loop by polling queue messages."""
        while True:
            source_key = self._pop_queued_source_key()
            if source_key is None:
                continue
            try:
                self.process_source_key(source_key)
            except Exception:
                logger.exception("Failed processing source key '%s'", source_key)

    def process_source_key(self, source_key: str) -> None:
        """Parse a single raw document key and publish downstream work."""
        if not source_key.startswith(self.raw_prefix) or source_key == self.raw_prefix:
            return

        doc_id = doc_id_from_source_key(source_key)
        destination_key = self._processed_key(doc_id)
        s3_namespace = f"s3://{self.storage_bucket}"
        self.lineage.start_run()
        self.lineage.add_input({"namespace": s3_namespace, "name": source_key})
        self.lineage.add_output({"namespace": s3_namespace, "name": destination_key})
        if self._processed_exists(destination_key):
            error_message = f"Processed document already exists: {destination_key}"
            self.stage_queue.push_dlq_message(
                storage_key=source_key,
                doc_id=doc_id,
                error=error_message,
                failed_at=utc_now_iso(),
            )
            self.lineage.fail_run(error_message=error_message)
            return

        try:
            payload = self._process_object(source_key, doc_id)
        except Exception as exc:
            error_message = str(exc)
            self.stage_queue.push_dlq_message(
                storage_key=source_key,
                doc_id=doc_id,
                error=error_message,
                failed_at=utc_now_iso(),
            )
            self.lineage.fail_run(error_message=error_message)
            logger.exception("Failed parsing source key '%s'; sent to DLQ", source_key)
            return
        self._write_processed_object(destination_key, payload)
        self._enqueue_processed_object(destination_key)
        self.lineage.complete_run()
        logger.info("Wrote processed document '%s'", destination_key)

    def _pop_queued_source_key(self) -> str | None:
        """Pop one source key from parse queue when available."""
        message = self.stage_queue.pop_message()
        if message is None:
            return None
        return str(message["storage_key"])

    def _processed_key(self, doc_id: str) -> str:
        """Build the processed-stage key for a document id."""
        return f"{self.processed_prefix}{doc_id}.json"

    def _processed_exists(self, destination_key: str) -> bool:
        """Return whether the processed output already exists."""
        return self.object_storage.object_exists(self.storage_bucket, destination_key)

    def _process_object(self, source_key: str, doc_id: str) -> dict[str, Any]:
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

    def _write_processed_object(self, destination_key: str, payload: dict[str, Any]) -> None:
        """Persist parsed document payload into the processed S3 stage."""
        self.object_storage.write_object(
            self.storage_bucket,
            destination_key,
            json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            content_type="application/json",
        )

    def _enqueue_processed_object(self, destination_key: str) -> None:
        """Publish chunking work for a newly produced processed document."""
        self.stage_queue.push_produce_message(storage_key=destination_key)

    def _initialize_runtime_config(self, processing_config: DocumentProcessingConfig) -> None:
        """Internal helper for initialize runtime config."""
        self.poll_interval_seconds = processing_config["poll_interval_seconds"]
        self.storage_bucket = processing_config["storage"]["bucket"]
        self.raw_prefix = processing_config["storage"]["raw_prefix"]
        self.processed_prefix = processing_config["storage"]["processed_prefix"]
        self.security_clearance = processing_config["security"]["clearance"]
