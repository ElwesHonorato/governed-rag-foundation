"""Worker service for worker_index_elasticsearch."""

from __future__ import annotations

from pipeline_common.elasticsearch import ElasticsearchIndexWorkItem
from pipeline_common.gateways.lineage import DatasetPlatform, LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import ConsumedMessage, QueueGateway
from pipeline_common.stages_contracts import ProcessResult
from pipeline_common.startup.contracts import WorkerService
from worker_index_elasticsearch.services.index_elasticsearch_processor import IndexElasticsearchProcessor


class WorkerIndexElasticsearchService(WorkerService):
    """Index chunk artifacts into Elasticsearch by polling a dedicated queue."""

    def __init__(
        self,
        *,
        stage_queue: QueueGateway,
        object_storage: ObjectStorageGateway,
        lineage: LineageRuntimeGateway,
        poll_interval_seconds: int,
        processor: IndexElasticsearchProcessor,
    ) -> None:
        """Initialize indexing worker dependencies and runtime settings."""
        self._queue_gateway = stage_queue
        self._object_storage = object_storage
        self._lineage_gateway = lineage
        self._poll_interval_seconds = poll_interval_seconds
        self._processor = processor

    def serve(self) -> None:
        """Run the Elasticsearch indexing worker loop by polling queue messages."""
        while True:
            message: ConsumedMessage | None = None
            lineage_started = False
            try:
                message = self._queue_gateway.wait_for_message(
                    poll_interval_seconds=self._poll_interval_seconds,
                )
                work_item = ElasticsearchIndexWorkItem.from_dict(message.payload)
                self._register_lineage_input(work_item.uri)
                lineage_started = True
                process_result = self._index_chunk_payload(work_item.uri)
                self._register_elasticsearch_output(process_result)
            except Exception as exc:
                if lineage_started:
                    self._lineage_gateway.fail_run(error_message=str(exc))
                if message is not None:
                    message.nack(requeue=True)
                continue
            message.ack()

    def _register_lineage_input(self, uri: str) -> None:
        """Start a lineage run and register the source chunk artifact."""
        self._lineage_gateway.start_run()
        self._lineage_gateway.add_input(name=uri, platform=DatasetPlatform.S3)

    def _index_chunk_payload(self, input_uri: str) -> ProcessResult:
        """Load one chunk artifact and index it into Elasticsearch."""
        raw_payload = self._object_storage.read_object(uri=input_uri)
        return self._processor.process(input_uri=input_uri, raw_payload=raw_payload)

    def _register_elasticsearch_output(self, process_result: ProcessResult) -> None:
        """Register the Elasticsearch sink as the output for one successful run."""
        self._lineage_gateway.add_output(
            name=str(process_result.result["elasticsearch_index"]),
            platform=DatasetPlatform.ELASTICSEARCH,
        )
        self._lineage_gateway.complete_run()
