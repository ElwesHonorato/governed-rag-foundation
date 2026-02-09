import time
from services.cycle_processor import CycleProcessor
from services.worker_service import WorkerService


class WorkerScanService(WorkerService):
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
            self.processor.scan()
            time.sleep(self.poll_interval_seconds)
