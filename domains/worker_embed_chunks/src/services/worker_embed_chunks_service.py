"""Worker service for worker_embed_chunks."""

from __future__ import annotations

import logging

from pipeline_common.gateways.lineage import DatasetPlatform, LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import ConsumedMessage, Envelope, QueueGateway
from pipeline_common.stages_contracts import ProcessResult
from pipeline_common.startup.contracts import WorkerService
from services.embed_flow import EmbedWorkItem
from services.embed_chunks_processor import EmbedChunksProcessor

logger = logging.getLogger(__name__)


class WorkerEmbedChunksService(WorkerService):
    """Transform chunk artifacts into embedding payloads."""

    def __init__(
        self,
        *,
        stage_queue: QueueGateway,
        object_storage: ObjectStorageGateway,
        lineage: LineageRuntimeGateway,
        poll_interval_seconds: int,
        processor: EmbedChunksProcessor,
    ) -> None:
        """Initialize embedding worker dependencies and runtime settings."""
        self._queue_gateway = stage_queue
        self._storage_gateway = object_storage
        self._lineage_gateway = lineage
        self._poll_interval_seconds = poll_interval_seconds
        self._processor = processor

    def serve(self) -> None:
        """Run the embedding worker loop by polling queue messages."""
        while True:
            message: ConsumedMessage | None = None
            lineage_started = False
            try:
                message = self._queue_gateway.wait_for_message(
                    poll_interval_seconds=self._poll_interval_seconds,
                )
                work_item = self._work_item_from_message(message)
                self._register_lineage_input(work_item.uri)
                lineage_started = True
                process_result: ProcessResult = self._transform_chunk_to_embeddings(work_item.uri)
                output_uri = self._output_uri_from_process_result(process_result)
                self._enqueue_embeddings_object(output_uri)
                self._register_embedding_output_lineage(output_uri)
            except Exception as exc:
                if lineage_started:
                    self._lineage_gateway.fail_run(error_message=str(exc))
                if message is not None:
                    message.nack(requeue=True)
                logger.exception("Embedding failed for input artifact")
                continue
            message.ack()

    def _register_lineage_input(self, uri: str) -> None:
        """Start a lineage run and register the source chunk artifact."""
        self._lineage_gateway.start_run()
        self._lineage_gateway.add_input(
            name=uri,
            platform=DatasetPlatform.S3,
        )

    def _register_embedding_output_lineage(self, uri: str) -> None:
        """Register the written embedding artifact as lineage output."""
        self._lineage_gateway.add_output(
            name=uri,
            platform=DatasetPlatform.S3,
        )
        self._lineage_gateway.complete_run()

    def _transform_chunk_to_embeddings(self, input_uri: str) -> ProcessResult:
        """Read one chunk artifact and build the embedding process result."""
        raw_payload = self._storage_gateway.read_object(uri=input_uri)
        process_result = self._processor.process(input_uri=input_uri, raw_payload=raw_payload)
        logger.info("Wrote embedding object '%s'", process_result.result["destination_key"])
        return process_result

    def _enqueue_embeddings_object(self, uri: str) -> None:
        self._queue_gateway.push(
            Envelope(
                payload=uri,
            ).to_payload
        )

    def _output_uri_from_process_result(self, process_result: ProcessResult) -> str:
        """Extract the written output URI from the process result."""
        return str(process_result.result["output_uri"])

    def _work_item_from_message(self, message: ConsumedMessage) -> EmbedWorkItem:
        """Parse source URI from queue payload."""
        envelope: Envelope = Envelope.from_dict(message.payload)
        return EmbedWorkItem(uri=str(envelope.payload))
