import logging
import time
from typing import Any

from pipeline_common.startup.contracts import WorkerPollingContract, WorkerService
from services.scan_cycle_processor import ScanCycleProcessor

logger = logging.getLogger(__name__)


class WorkerScanService(WorkerService):
    """Run scan cycles repeatedly using the configured processor."""
    def __init__(
        self,
        *,
        processor: ScanCycleProcessor,
        polling_contract: WorkerPollingContract,
        spark_session: Any | None,
    ) -> None:
        """Initialize instance state and dependencies."""
        self.processor = processor
        self.poll_interval_seconds = polling_contract.poll_interval_seconds
        self.spark_session = spark_session

    def serve(self) -> None:
        """Run the worker loop indefinitely."""
        while True:
            try:
                self.processor.scan()
            except Exception:
                logger.exception("Scan cycle failed; continuing after poll interval")
            time.sleep(self.poll_interval_seconds)
