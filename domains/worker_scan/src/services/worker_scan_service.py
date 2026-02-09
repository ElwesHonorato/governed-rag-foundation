from __future__ import annotations

import time
from typing import Protocol


class CycleProcessor(Protocol):
    def process_once(self) -> int:
        ...


class WorkerScanService:
    def __init__(
        self,
        *,
        processor: CycleProcessor,
        poll_interval_seconds: int,
    ) -> None:
        self.processor = processor
        self.poll_interval_seconds = poll_interval_seconds

    def run_forever(self) -> None:
        while True:
            self.processor.process_once()
            time.sleep(self.poll_interval_seconds)
