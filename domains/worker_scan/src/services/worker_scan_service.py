import logging
import time

from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import Envelope, QueueGateway
from pipeline_common.helpers.contracts import doc_id_from_source_key
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
            self._run_scan_iteration()

    def _run_scan_iteration(self) -> None:
        self._execute_scan_cycle()
        self._sleep_until_next_cycle()

    def _execute_scan_cycle(self) -> None:
        try:
            source_keys = self._storage_gateway.list_keys(self._processor.bucket, self._processor.source_prefix)
            processed = 0
            for work_item in self._processor.plan_work(source_keys):
                processed += int(self._process_work_item(work_item))
            logger.info("Scan cycle processed %d item(s)", processed)
        except Exception:
            self._handle_scan_cycle_failure()

    def _process_work_item(self, work_item: ScanWorkItem) -> bool:
        if not self._storage_gateway.object_exists(self._processor.bucket, work_item.source_key):
            return False

        self._register_lineage_input(work_item)
        try:
            self._storage_gateway.copy(
                self._processor.bucket,
                work_item.source_key,
                work_item.destination_key,
            )
            self._register_lineage_output(work_item)
            destination_uri = self._storage_gateway.build_uri(self._processor.bucket, work_item.destination_key)
            self._queue_gateway.push(
                Envelope(
                    payload=destination_uri,
                ).to_payload
            )
            self._storage_gateway.delete(self._processor.bucket, work_item.source_key)
            logger.info(
                "Moved '%s' -> '%s' (source_doc_id=%s, dest_doc_id=%s)",
                work_item.source_key,
                work_item.destination_key,
                doc_id_from_source_key(work_item.source_key),
                doc_id_from_source_key(work_item.destination_key),
            )
            return True
        except Exception:
            self._lineage_gateway.abort_run()
            raise

    def _register_lineage_input(self, work_item: ScanWorkItem) -> None:
        """Start a lineage run and register the source object."""
        self._lineage_gateway.start_run()
        self._lineage_gateway.add_input(
            name=self._storage_gateway.build_uri(self._processor.bucket, work_item.source_key),
            platform=DatasetPlatform.S3,
        )

    def _register_lineage_output(self, work_item: ScanWorkItem) -> None:
        """Register the promoted object as lineage output and complete the run."""
        self._lineage_gateway.add_output(
            name=self._storage_gateway.build_uri(self._processor.bucket, work_item.destination_key),
            platform=DatasetPlatform.S3,
        )
        self._lineage_gateway.complete_run()

    def _handle_scan_cycle_failure(self) -> None:
        logger.exception("Scan cycle failed; continuing after poll interval")

    def _sleep_until_next_cycle(self) -> None:
        time.sleep(self._poll_interval_seconds)
