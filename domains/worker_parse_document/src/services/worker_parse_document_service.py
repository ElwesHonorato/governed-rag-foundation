import logging
import json
from typing import Any

from contracts.contracts import ParseProcessingConfigContract
from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import ConsumedMessage, Envelope, QueueGateway
from pipeline_common.helpers.contracts import doc_id_from_source_key, utc_now_iso
from pipeline_common.provenance import source_content_hash
from pipeline_common.startup.contracts import WorkerService
from parsing.registry import ParserRegistry
from services.parse_flow_components import (
    DocumentParserProcessor,
    ParseOutputMessageFactory,
    ParseWorkItem,
)

logger = logging.getLogger(__name__)


class WorkerParseDocumentService(WorkerService):
    """Transform raw source documents into processed payloads."""

    def __init__(
        self,
        *,
        stage_queue: QueueGateway,
        object_storage: ObjectStorageGateway,
        lineage: LineageRuntimeGateway,
        spark_session: Any | None,
        processing_config: ParseProcessingConfigContract,
        parser_registry: ParserRegistry,
    ) -> None:
        """Initialize parse worker dependencies and runtime settings."""
        self.stage_queue = stage_queue
        self.object_storage = object_storage
        self.lineage = lineage
        self.spark_session = spark_session
        self.parser_registry = parser_registry
        self._initialize_runtime_config(processing_config)
        self.parser_processor = DocumentParserProcessor(
            parser_registry=self.parser_registry,
            security_clearance=self.security_clearance,
            spark_session=self.spark_session,
        )

    def serve(self) -> None:
        """Run the parse worker loop by polling queue messages."""
        while True:
            message = self.stage_queue.pop_message()
            if message is None:
                continue
            try:
                source_key = self._source_key_from_message(message)
            except Exception:
                message.nack(requeue=True)
                logger.exception("Failed parse invalid-message handling; requeued message")
                continue
            if source_key is None:
                continue
            try:
                self._handle_parse_request(source_key)
            except Exception:
                message.nack(requeue=True)
                logger.exception("Failed processing source key '%s'; requeued message", source_key)
                continue
            message.ack()

    def _handle_parse_request(self, source_key: str) -> None:
        """Orchestrate one parse unit: read -> parse -> write -> enqueue."""
        parse_job = self._build_parse_job(source_key)
        if parse_job is None:
            return

        self._start_parse_lineage(parse_job)
        if self._skip_if_destination_exists(parse_job):
            return

        try:
            payload = self._build_processed_payload(parse_job)
            self._write_processed_payload(parse_job, payload)
            self._publish_parse_output(parse_job)
            self.lineage.complete_run()
            logger.info("Wrote processed document '%s'", parse_job.destination_key)
        except Exception as exc:
            self._handle_parse_failure(parse_job, str(exc))
            logger.exception("Failed parsing source key '%s'; sent to DLQ", parse_job.source_key)

    def _start_parse_lineage(self, parse_job: ParseWorkItem) -> None:
        self.lineage.start_run()
        self.lineage.add_input(
            name=f"{self.storage_bucket}/{parse_job.source_key}",
            platform=DatasetPlatform.S3,
        )

    def _skip_if_destination_exists(self, parse_job: ParseWorkItem) -> bool:
        if not self.object_storage.object_exists(self.storage_bucket, parse_job.destination_key):
            return False
        logger.info(
            "Skipping parse for source '%s' because destination already exists: '%s'",
            parse_job.source_key,
            parse_job.destination_key,
        )
        self.lineage.complete_run()
        return True

    def _build_processed_payload(self, parse_job: ParseWorkItem) -> dict[str, Any]:
        source_uri = "s3a://{bucket}/{source_key}".format(
            bucket=self.storage_bucket,
            source_key=parse_job.source_key,
        )
        raw_payload = self.object_storage.read_object(source_uri)
        raw_text = raw_payload.decode("utf-8", errors="ignore")
        return self.parser_processor.build_payload(
            source_key=parse_job.source_key,
            doc_id=parse_job.doc_id,
            raw_text=raw_text,
            raw_content_hash=source_content_hash(raw_payload),
            timestamp=utc_now_iso(),
        )

    def _write_processed_payload(self, parse_job: ParseWorkItem, payload: dict[str, Any]) -> None:
        self.object_storage.write_object(
            self.storage_bucket,
            parse_job.destination_key,
            json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            content_type="application/json",
        )
        self.lineage.add_output(
            name=f"{self.storage_bucket}/{parse_job.destination_key}",
            platform=DatasetPlatform.S3,
        )

    def _publish_parse_output(self, parse_job: ParseWorkItem) -> None:
        source_uri = "s3a://{bucket}/{source_key}".format(
            bucket=self.storage_bucket,
            source_key=parse_job.destination_key,
        )
        self.stage_queue.push(ParseOutputMessageFactory.build(source_uri=source_uri).to_payload)

    def _handle_parse_failure(self, parse_job: ParseWorkItem, error_message: str) -> None:
        self.stage_queue.push_dlq(
            Envelope(
                type="parse_document.failure",
                payload={
                    "source_key": parse_job.source_key,
                    "doc_id": parse_job.doc_id,
                    "error": error_message,
                    "failed_at": utc_now_iso(),
                },
            )
            .to_payload
        )
        self.lineage.fail_run(error_message=error_message)

    def _build_parse_job(self, source_key: str) -> ParseWorkItem | None:
        doc_id = doc_id_from_source_key(source_key)
        destination_key = f"{self.output_prefix}{doc_id}.json"
        return ParseWorkItem(source_key=source_key, doc_id=doc_id, destination_key=destination_key)

    def _source_key_from_message(self, message: ConsumedMessage) -> str | None:
        """Parse source key from queue payload; route invalid payloads to DLQ."""
        try:
            envelope = Envelope.from_dict(message.payload)
            return str(envelope.payload["storage_key"])
        except Exception as exc:
            self.stage_queue.push_dlq(
                Envelope(
                    type="parse_document.invalid_message",
                    payload={
                        "error": str(exc),
                        "message_payload": message.payload,
                        "failed_at": utc_now_iso(),
                    },
                ).to_payload
            )
            message.ack()
            logger.exception("Invalid parse queue message payload; sent to DLQ and acknowledged")
            return None

    def _initialize_runtime_config(self, processing_config: ParseProcessingConfigContract) -> None:
        """Internal helper for initialize runtime config."""
        self.poll_interval_seconds = processing_config.poll_interval_seconds
        self.storage_bucket = processing_config.storage.bucket
        self.output_prefix = processing_config.storage.output_prefix
        self.security_clearance = processing_config.security.clearance
