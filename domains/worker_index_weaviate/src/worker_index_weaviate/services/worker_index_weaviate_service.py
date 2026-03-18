"""Worker service for worker_index_weaviate."""

from __future__ import annotations

from pipeline_common.gateways.lineage import DatasetPlatform, LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import ConsumedMessage, Envelope, QueueGateway
from pipeline_common.stages_contracts import ProcessResult
from pipeline_common.startup.contracts import WorkerService
from worker_index_weaviate.services.index_flow import IndexWorkItem
from worker_index_weaviate.services.index_weaviate_processor import IndexWeaviateProcessor


class WorkerIndexWeaviateService(WorkerService):
    """Index embeddings artifacts into Weaviate and persist status objects."""

    def __init__(
        self,
        *,
        stage_queue: QueueGateway,
        object_storage: ObjectStorageGateway,
        lineage: LineageRuntimeGateway,
        poll_interval_seconds: int,
        processor: IndexWeaviateProcessor,
    ) -> None:
        """Initialize indexing worker dependencies and runtime settings."""
        self._queue_gateway = stage_queue
        self._storage_gateway = object_storage
        self._lineage_gateway = lineage
        self._poll_interval_seconds = poll_interval_seconds
        self._processor = processor

    def serve(self) -> None:
        """Run the indexing worker loop by polling queue messages."""
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
                process_result: ProcessResult = self._index_embeddings_payload(work_item.uri)
                self._register_index_output_lineage(self._output_uri_from_process_result(process_result))
            except Exception as exc:
                if lineage_started:
                    self._lineage_gateway.fail_run(error_message=str(exc))
                if message is not None:
                    message.nack(requeue=True)
                continue
            message.ack()

    def _register_lineage_input(self, uri: str) -> None:
        """Start a lineage run and register the source embeddings artifact."""
        self._lineage_gateway.start_run()
        self._lineage_gateway.add_input(
            name=uri,
            platform=DatasetPlatform.S3,
        )

    def _register_index_output_lineage(self, uri: str) -> None:
        """Register the written index status artifact and Weaviate sink as outputs."""
        self._lineage_gateway.add_output(
            name=uri,
            platform=DatasetPlatform.S3,
        )
        self._lineage_gateway.add_output(
            name=self._processor.weaviate_output_name(),
            platform=DatasetPlatform.WEAVIATE,
        )
        self._lineage_gateway.complete_run()

    def _index_embeddings_payload(self, input_uri: str) -> ProcessResult:
        """Read one embeddings artifact and build the indexing process result."""
        raw_payload = self._storage_gateway.read_object(uri=input_uri)
        return self._processor.process(input_uri=input_uri, raw_payload=raw_payload)

    def _output_uri_from_process_result(self, process_result: ProcessResult) -> str:
        """Extract the written output URI from the process result."""
        return str(process_result.result["output_uri"])

    def _work_item_from_message(self, message: ConsumedMessage) -> IndexWorkItem:
        """Parse index request from queue payload."""
        envelope: Envelope = Envelope.from_dict(message.payload)
        return IndexWorkItem(uri=str(envelope.payload))
