"""Service graph assembly for worker_scan startup."""

from contracts.contracts import ScanStorageContract, ScanWorkerConfigContract
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import QueueGateway
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
        stage_queue: QueueGateway = runtime.stage_queue_gateway
        object_storage: ObjectStorageGateway = runtime.object_storage_gateway
        lineage_gateway: LineageRuntimeGateway = runtime.lineage_gateway

        # Keep startup side effect explicit and early.
        object_storage.bootstrap_bucket_prefixes(worker_config.storage.bucket)

        storage_contract: ScanStorageContract = ScanStorageContract(
            bucket=worker_config.storage.bucket,
            source_prefix=worker_config.storage.source_prefix,
            output_prefix=worker_config.storage.output_prefix,
        )
        polling_contract: WorkerPollingContract = WorkerPollingContract(
            poll_interval_seconds=worker_config.poll_interval_seconds,
        )
        processor: StorageScanCycleProcessor = StorageScanCycleProcessor(
            storage_contract=storage_contract,
        )
        return WorkerScanService(
            processor=processor,
            stage_queue=stage_queue,
            object_storage=object_storage,
            lineage=lineage_gateway,
            polling_contract=polling_contract,
        )
