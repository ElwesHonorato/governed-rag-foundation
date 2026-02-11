from abc import ABC, abstractmethod
import time
from typing import TypedDict
from services.scan_cycle_processor import ScanCycleProcessor


class WorkerService(ABC):
    @abstractmethod
    def serve(self) -> None:
        """Run the worker loop indefinitely."""


class ScanProcessingConfig(TypedDict):
    poll_interval_seconds: int


class WorkerScanService(WorkerService):
    def __init__(
        self,
        *,
        processor: ScanCycleProcessor,
        processing_config: ScanProcessingConfig,
    ) -> None:
        self.processor = processor
        self._initialize_runtime_config(processing_config)

    def serve(self) -> None:
        while True:
            self.processor.scan()
            time.sleep(self.poll_interval_seconds)

    def _initialize_runtime_config(self, processing_config: ScanProcessingConfig) -> None:
        self.poll_interval_seconds = processing_config["poll_interval_seconds"]
