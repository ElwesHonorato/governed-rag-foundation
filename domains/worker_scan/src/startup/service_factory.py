"""Service graph assembly for worker_scan startup."""

from contracts.contracts import ScanStorageContract, ScanWorkerConfigContract
from pipeline_common.startup import WorkerPollingContract, WorkerRuntimeContext, WorkerServiceFactory
from services.scan_cycle_processor import StorageScanCycleProcessor
from services.worker_scan_service import WorkerScanService


class ScanServiceFactory(WorkerServiceFactory[ScanWorkerConfigContract, WorkerScanService]):
    """Build scan service from runtime context and typed scan config."""

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: ScanWorkerConfigContract,
    ) -> WorkerScanService:
        """Construct worker scan service object graph."""
        stage_queue = runtime.stage_queue_gateway
        object_storage = runtime.object_storage_gateway
        lineage_gateway = runtime.lineage_gateway

        # Keep startup side effect explicit and early.
        object_storage.bootstrap_bucket_prefixes(worker_config.storage.bucket)

        processor = StorageScanCycleProcessor(
            object_storage=object_storage,
            stage_queue=stage_queue,
            lineage=lineage_gateway,
            storage_contract=ScanStorageContract(
                bucket=worker_config.storage.bucket,
                input_prefix=worker_config.storage.input_prefix,
                output_prefix=worker_config.storage.output_prefix,
            ),
        )
        return WorkerScanService(
            processor=processor,
            polling_contract=WorkerPollingContract(
                poll_interval_seconds=worker_config.poll_interval_seconds,
            ),
        )
