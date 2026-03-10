import logging
import time
from typing import Any

from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import Envelope, StageQueue
from pipeline_common.helpers.contracts import doc_id_from_source_key
from pipeline_common.startup.contracts import WorkerPollingContract, WorkerService
from services.scan_cycle_processor import StorageScanCycleProcessor

logger = logging.getLogger(__name__)


class WorkerScanService(WorkerService):
    """Run scan cycles repeatedly using the configured processor."""
    def __init__(
        self,
        *,
        processor: StorageScanCycleProcessor,
        stage_queue: StageQueue,
        object_storage: ObjectStorageGateway,
        lineage: LineageRuntimeGateway,
        polling_contract: WorkerPollingContract,
        spark_session: Any | None,
    ) -> None:
        """Initialize instance state and dependencies."""
        self.processor = processor
        self.stage_queue = stage_queue
        self.object_storage = object_storage
        self.lineage = lineage
        self.poll_interval_seconds = polling_contract.poll_interval_seconds
        self.spark_session = spark_session

    def serve(self) -> None:
        """Run the worker loop indefinitely."""
        while True:
            self._run_scan_iteration()

    def _run_scan_iteration(self) -> None:
        self._execute_scan_cycle()
        self._sleep_until_next_cycle()

    def _execute_scan_cycle(self) -> None:
        try:
            source_keys = self.object_storage.list_keys(self.processor.bucket, self.processor.source_prefix)
            processed = 0
            for source_key in self.processor.candidate_keys(source_keys):
                processed += int(self._process_source_key(source_key))
            logger.info("Scan cycle processed %d item(s)", processed)
        except Exception:
            self._handle_scan_cycle_failure()

    def _process_source_key(self, source_key: str) -> bool:
        if not self.object_storage.object_exists(self.processor.bucket, source_key):
            return False

        destination_key = self.processor.destination_key(source_key)
        self.lineage.start_run()
        self.lineage.add_input(
            name=f"{self.processor.bucket}/{source_key}",
            platform=DatasetPlatform.S3,
        )
        self.lineage.add_output(
            name=f"{self.processor.bucket}/{destination_key}",
            platform=DatasetPlatform.S3,
        )
        try:
            self.object_storage.copy(self.processor.bucket, source_key, destination_key)
            self.lineage.complete_run()
            self.stage_queue.push(
                Envelope(
                    type="parse_document.request",
                    payload={"storage_key": destination_key},
                ).to_payload
            )
            self.object_storage.delete(self.processor.bucket, source_key)
            logger.info(
                "Moved '%s' -> '%s' (source_doc_id=%s, dest_doc_id=%s)",
                source_key,
                destination_key,
                doc_id_from_source_key(source_key),
                doc_id_from_source_key(destination_key),
            )
            return True
        except Exception:
            self.lineage.abort_run()
            raise

    def _handle_scan_cycle_failure(self) -> None:
        logger.exception("Scan cycle failed; continuing after poll interval")

    def _sleep_until_next_cycle(self) -> None:
        time.sleep(self.poll_interval_seconds)
