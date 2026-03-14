"""Service graph assembly for worker_scan startup."""

from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from services.scan_cycle_processor import StorageScanCycleProcessor
from services.worker_scan_service import WorkerScanService
from startup.contracts import RuntimeScanJobConfig


class ScanServiceFactory(WorkerServiceFactory[RuntimeScanJobConfig, WorkerScanService]):
    """Build scan service from runtime context and typed scan config."""

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: RuntimeScanJobConfig,
    ) -> WorkerScanService:
        """Construct worker scan service object graph."""
        # Keep startup side effect explicit and early.
        runtime.object_storage_gateway.bootstrap_bucket_prefixes(worker_config.storage.bucket)
        processor: StorageScanCycleProcessor = StorageScanCycleProcessor(
            storage_config=worker_config.storage,
        )
        return WorkerScanService(
            processor=processor,
            stage_queue=runtime.stage_queue_gateway,
            object_storage=runtime.object_storage_gateway,
            lineage=runtime.lineage_gateway,
            poll_interval_seconds=worker_config.poll_interval_seconds,
        )
