import logging
import mimetypes
import time
from pathlib import Path

from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import Envelope, QueueGateway
from pipeline_common.helpers.contracts import doc_id_from_source_key
from pipeline_common.stages_contracts import ProcessResult, ProcessorContext, SourceDocumentMetadata
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
                source_keys = self._storage_gateway.list_keys(
                    self._processor.bucket,
                    self._processor.source_prefix,
                )
                processed = 0
                for source_key in source_keys:
                    work_item = ScanWorkItem(
                        source_key=source_key,
                        destination_key=self._processor.destination_key(source_key),
                    )
                    process_result: ProcessResult = self._promote_source_object(work_item)
                    output_uri = self._output_uri_from_process_result(process_result)
                    self._publish_scan_output(output_uri)
                    self._register_lineage_output(output_uri)
                    processed += 1
                logger.info("Scan cycle processed %d item(s)", processed)
            except Exception:
                self._handle_scan_cycle_failure()
            self._sleep_until_next_cycle()

    def _promote_source_object(self, work_item: ScanWorkItem) -> ProcessResult:
        """Promote one source object and return the process result."""
        self._register_lineage_input(work_item)
        self._storage_gateway.copy(
            self._processor.bucket,
            work_item.source_key,
            work_item.destination_key,
        )
        self._storage_gateway.delete(self._processor.bucket, work_item.source_key)
        logger.info(
            "Moved '%s' -> '%s' (source_doc_id=%s, dest_doc_id=%s)",
            work_item.source_key,
            work_item.destination_key,
            doc_id_from_source_key(work_item.source_key),
            doc_id_from_source_key(work_item.destination_key),
        )
        return ProcessResult(
            run_id=work_item.destination_key,
            source_metadata=SourceDocumentMetadata.build(
                doc_id=doc_id_from_source_key(work_item.source_key),
                source_key=work_item.source_key,
                timestamp="",
                security_clearance="",
                source_type=Path(work_item.source_key).suffix.lower().lstrip("."),
                content_type=str(mimetypes.guess_type(work_item.source_key)[0] or "application/octet-stream"),
                source_content_hash="",
            ),
            input_uri=self._storage_gateway.build_uri(self._processor.bucket, work_item.source_key),
            processor_context=ProcessorContext(params_hash="", params=[]),
            processor=ProcessorMetadata(name="StorageScanCycleProcessor", version="1.0.0"),
            result={
                "output_uri": self._storage_gateway.build_uri(self._processor.bucket, work_item.destination_key),
            },
        )

    def _register_lineage_input(self, work_item: ScanWorkItem) -> None:
        """Start a lineage run and register the source object."""
        self._lineage_gateway.start_run()
        self._lineage_gateway.add_input(
            name=self._storage_gateway.build_uri(self._processor.bucket, work_item.source_key),
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

    def _handle_scan_cycle_failure(self) -> None:
        logger.exception("Scan cycle failed; continuing after poll interval")

    def _sleep_until_next_cycle(self) -> None:
        time.sleep(self._poll_interval_seconds)
