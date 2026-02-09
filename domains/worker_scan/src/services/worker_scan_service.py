from abc import ABC, abstractmethod
import time
from services.scan_cycle_processor import ScanCycleProcessor


class WorkerService(ABC):
    @abstractmethod
    def run_forever(self) -> None:
        """Run the worker loop indefinitely."""


class WorkerScanService(WorkerService):
    def __init__(
        self,
        *,
        processor: ScanCycleProcessor,
        poll_interval_seconds: int,
    ) -> None:
        self.processor = processor
        self.poll_interval_seconds = poll_interval_seconds

    def run_forever(self) -> None:
        while True:
            self.processor.scan()
            time.sleep(self.poll_interval_seconds)
