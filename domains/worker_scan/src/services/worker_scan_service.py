from abc import ABC, abstractmethod

import time
from typing import TypedDict
from services.scan_cycle_processor import ScanCycleProcessor


class WorkerService(ABC):
    """Minimal worker interface for long-running service loops."""

    @abstractmethod
    def serve(self) -> None:
        """Run the worker loop indefinitely."""


class ScanProcessingConfig(TypedDict):
    """Runtime config for scan worker polling."""
    poll_interval_seconds: int


class WorkerScanService(WorkerService):
    """Run scan cycles repeatedly using the configured processor."""
    def __init__(
        self,
        *,
        processor: ScanCycleProcessor,
        processing_config: ScanProcessingConfig,
    ) -> None:
        """Initialize instance state and dependencies."""
        self.processor = processor
        self._initialize_runtime_config(processing_config)

    def serve(self) -> None:
        """Run the worker loop indefinitely."""
        while True:
            self.processor.scan()
            time.sleep(self.poll_interval_seconds)

    def _initialize_runtime_config(self, processing_config: ScanProcessingConfig) -> None:
        """Internal helper for initialize runtime config."""
        self.poll_interval_seconds = processing_config["poll_interval_seconds"]
