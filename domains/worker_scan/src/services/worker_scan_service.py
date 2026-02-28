from dataclasses import dataclass

import logging
import time
from pipeline_common.startup.contracts import WorkerService
from services.scan_cycle_processor import ScanCycleProcessor

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScanPollingContract:
    """Polling cadence contract for scan worker service loop."""

    poll_interval_seconds: int


class WorkerScanService(WorkerService):
    """Run scan cycles repeatedly using the configured processor."""
    def __init__(
        self,
        *,
        processor: ScanCycleProcessor,
        polling_contract: ScanPollingContract,
    ) -> None:
        """Initialize instance state and dependencies."""
        self.processor = processor
        self.poll_interval_seconds = polling_contract.poll_interval_seconds

    def serve(self) -> None:
        """Run the worker loop indefinitely."""
        while True:
            try:
                self.processor.scan()
            except Exception:
                logger.exception("Scan cycle failed; continuing after poll interval")
            time.sleep(self.poll_interval_seconds)
