import logging
import time

from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import Envelope, QueueGateway
from pipeline_common.helpers.contracts import doc_id_from_source_uri, utc_now_iso
from pipeline_common.stages_contracts import FileMetadata, ProcessResult, ProcessorContext
from pipeline_common.stages_contracts.step_00_common import ProcessorMetadata
from pipeline_common.startup.contracts import WorkerService
from services.scan_cycle_processor import ScanWorkItem, StorageScanCycleProcessor

logger = logging.getLogger(__name__)


class WorkerScanService(WorkerService):
    """Run scan cycles repeatedly using the configured processor."""
    def __init__(
        self,
        *,
        processor: StorageScanCycleProcessor,
        stage_queue: QueueGateway,
        object_storage: ObjectStorageGateway,
        lineage: LineageRuntimeGateway,
        poll_interval_seconds: int,
    ) -> None:
        """Initialize instance state and dependencies."""
        self._processor = processor
        self._queue_gateway = stage_queue
        self._storage_gateway = object_storage
        self._lineage_gateway = lineage
        self._poll_interval_seconds = poll_interval_seconds

    def serve(self) -> None:
        """Run the worker loop indefinitely."""
        while True:
            try:
                keys = self._storage_gateway.list_keys(
                    self._processor.bucket,
                    self._processor.source_prefix,
                )
                processed = 0
                for key in keys:
                    work_item = self._build_work_item(key)
                    process_result: ProcessResult = self._move_file(work_item)
                    output_uri = self._output_uri_from_process_result(process_result)
                    self._publish_scan_output(output_uri)
                    self._register_lineage_output(output_uri)
                    processed += 1
                logger.info("Scan cycle processed %d item(s)", processed)
            except Exception:
                self._handle_scan_cycle_failure()
            self._sleep_until_next_cycle()

    def _move_file(self, work_item: ScanWorkItem) -> ProcessResult:
        """Move one source object to its destination and return the process result."""
        raw_payload = self._storage_gateway.read_object(uri=work_item.source_uri)
        self._register_lineage_input(work_item.source_uri)
        self._storage_gateway.copy_object(work_item.source_uri, work_item.destination_uri)
        self._storage_gateway.delete_object(work_item.source_uri)
        logger.info(
            "Moved '%s' -> '%s' (source_doc_id=%s, dest_doc_id=%s)",
            work_item.source_uri,
            work_item.destination_uri,
            doc_id_from_source_uri(work_item.source_uri),
            doc_id_from_source_uri(work_item.destination_uri),
        )
        return ProcessResult(
            run_id=work_item.destination_uri,
            root_doc_metadata=FileMetadata.from_source_bytes(
                uri=work_item.source_uri,
                payload=raw_payload,
                default_content_type="application/octet-stream",
            ),
            stage_doc_metadata=FileMetadata.from_source_bytes(
                uri=work_item.source_uri,
                payload=raw_payload,
                default_content_type="application/octet-stream",
            ),
            input_uri=work_item.source_uri,
            processor_context=ProcessorContext(params_hash="", params=[]),
            processor=ProcessorMetadata(name="StorageScanCycleProcessor", version="1.0.0"),
            result={
                "output_uri": work_item.destination_uri,
            },
        )

    def _register_lineage_input(self, uri: str) -> None:
        """Start a lineage run and register the source object."""
        self._lineage_gateway.start_run()
        self._lineage_gateway.add_input(
            name=uri,
            platform=DatasetPlatform.S3,
        )

    def _register_lineage_output(self, uri: str) -> None:
        """Register the promoted object as lineage output and complete the run."""
        self._lineage_gateway.add_output(
            name=uri,
            platform=DatasetPlatform.S3,
        )
        self._lineage_gateway.complete_run()

    def _publish_scan_output(self, uri: str) -> None:
        """Publish the promoted object URI to the downstream queue."""
        self._queue_gateway.push(
            Envelope(
                payload=uri,
            ).to_payload
        )

    def _output_uri_from_process_result(self, process_result: ProcessResult) -> str:
        """Extract the written output URI from the process result."""
        return str(process_result.result["output_uri"])

    def _build_work_item(self, key: str) -> ScanWorkItem:
        destination_key = self._processor.destination_key(key)
        return ScanWorkItem(
            source_uri=self._storage_gateway.build_uri(self._processor.bucket, key),
            destination_uri=self._storage_gateway.build_uri(self._processor.bucket, destination_key),
        )

    def _handle_scan_cycle_failure(self) -> None:
        logger.exception("Scan cycle failed; continuing after poll interval")

    def _sleep_until_next_cycle(self) -> None:
        time.sleep(self._poll_interval_seconds)
