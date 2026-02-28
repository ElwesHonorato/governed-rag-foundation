from abc import ABC, abstractmethod
from dataclasses import dataclass

import logging
import time
from services.scan_cycle_processor import ScanCycleProcessor

logger = logging.getLogger(__name__)


class WorkerService(ABC):
    """Minimal worker interface for long-running service loops."""

    @abstractmethod
    def serve(self) -> None:
        """Run the worker loop indefinitely."""


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
