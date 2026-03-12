import logging
from typing import Any

from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import ConsumedMessage, Envelope, QueueGateway
from pipeline_common.helpers.contracts import doc_id_from_source_uri, utc_now_iso
from pipeline_common.provenance import source_content_hash
from pipeline_common.stages_contracts import ProcessResult, ProcessorContext, StageArtifact
from pipeline_common.startup.contracts import WorkerService
from services.parse_flow_components import (
    DocumentParserProcessor,
)
from services.parse_output import (
    ParseWorkItem,
    ParseOutputWriter,
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
        poll_interval_seconds: int,
        storage_bucket: str,
        output_prefix: str,
        parser_processor: DocumentParserProcessor,
        output_writer: ParseOutputWriter,
    ) -> None:
        """Initialize parse worker dependencies and runtime settings."""
        self._queue_gateway = stage_queue
        self._storage_gateway = object_storage
        self._lineage_gateway = lineage
        self._poll_interval_seconds = poll_interval_seconds
        self._storage_bucket = storage_bucket
        self._output_prefix = output_prefix
        self._parser_processor = parser_processor
        self._output_writer = output_writer

    def serve(self) -> None:
        """Run the parse worker loop by polling queue messages."""
        while True:
            message = self._queue_gateway.wait_for_message(
                poll_interval_seconds=self._poll_interval_seconds,
            )
            input_uri = self._input_uri_from_message(message)
            try:
                parse_job = self._build_parse_job(input_uri)
                self._register_lineage_input(parse_job)
                process_result: ProcessResult = self._transform_source_to_processed_document(parse_job)
                self._write_processed_payload(process_result)
                self._publish_parse_output(process_result)
                self._register_parse_output_lineage(process_result)
                logger.info("Wrote processed document '%s'", parse_job.destination_key)
            except Exception as exc:
                self._handle_parse_failure(input_uri, error_message=str(exc))
                message.nack(requeue=True)
                logger.exception("Failed processing input URI '%s'; requeued message", input_uri)
                continue
            message.ack()

    def _register_lineage_input(self, parse_job: ParseWorkItem) -> None:
        """Start a lineage run and register the source document."""
        self._lineage_gateway.start_run()
        self._lineage_gateway.add_input(
            name=parse_job.input_uri,
            platform=DatasetPlatform.S3,
        )

    def _transform_source_to_processed_document(self, parse_job: ParseWorkItem) -> ProcessResult:
        """Build the process result for one parsed document."""
        raw_payload = self._storage_gateway.read_object(uri=parse_job.input_uri)
        raw_text = raw_payload.decode("utf-8", errors="ignore")
        payload = self._parser_processor.build_payload(
            source_uri=parse_job.input_uri,
            doc_id=parse_job.doc_id,
            raw_text=raw_text,
            raw_content_hash=source_content_hash(raw_payload),
            timestamp=utc_now_iso(),
        )
        artifact = StageArtifact.from_dict(payload)
        return ProcessResult(
            run_id=parse_job.doc_id,
            root_metadata=artifact.root_metadata,
            input_uri=parse_job.input_uri,
            processor_context=ProcessorContext(params_hash="", params=[]),
            processor=artifact.processor_metadata,
            result={
                "payload": payload,
                "destination_key": parse_job.destination_key,
            },
        )

    def _write_processed_payload(self, process_result: ProcessResult) -> None:
        self._output_writer.write(
            destination_key=str(process_result.result["destination_key"]),
            payload=dict(process_result.result["payload"]),
        )

    def _register_parse_output_lineage(self, process_result: ProcessResult) -> None:
        """Register the written processed artifact as lineage output."""
        self._lineage_gateway.add_output(
            name=self._storage_gateway.build_uri(
                self._storage_bucket,
                str(process_result.result["destination_key"]),
            ),
            platform=DatasetPlatform.S3,
        )
        self._lineage_gateway.complete_run()

    def _publish_parse_output(self, process_result: ProcessResult) -> None:
        self._queue_gateway.push(
            self._output_writer.build_output_message(
                destination_key=str(process_result.result["destination_key"])
            ).to_payload
        )

    def _handle_parse_failure(self, input_uri: str, *, error_message: str) -> None:
        self._queue_gateway.push_dlq(
            Envelope(
                payload={
                    "uri": input_uri,
                    "error": error_message,
                    "failed_at": utc_now_iso(),
                },
            )
            .to_payload
        )
        self._lineage_gateway.fail_run(error_message=error_message)

    def _build_parse_job(self, input_uri: str) -> ParseWorkItem:
        doc_id = doc_id_from_source_uri(input_uri)
        destination_key = f"{self._output_prefix}{doc_id}.json"
        return ParseWorkItem(
            input_uri=input_uri,
            doc_id=doc_id,
            destination_key=destination_key,
        )

    def _input_uri_from_message(self, message: ConsumedMessage) -> str:
        """Parse input URI from queue payload."""
        envelope: Envelope = Envelope.from_dict(message.payload)
        return str(envelope.payload)
