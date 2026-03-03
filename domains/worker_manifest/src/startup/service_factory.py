"""Service graph assembly for worker_manifest startup."""

from contracts.contracts import ManifestProcessingConfigContract, ManifestWorkerConfigContract
from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from services.worker_manifest_service import WorkerManifestService


class ManifestServiceFactory(WorkerServiceFactory[ManifestWorkerConfigContract, WorkerManifestService]):
    """Build manifest service from runtime context and typed config."""

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: ManifestWorkerConfigContract,
    ) -> WorkerManifestService:
        """Construct worker manifest service object graph."""
        return WorkerManifestService(
            object_storage=runtime.object_storage_gateway,
            lineage=runtime.lineage_gateway,
            spark_session=runtime.spark_session,
            processing_config=ManifestProcessingConfigContract(
                poll_interval_seconds=worker_config.poll_interval_seconds,
                storage=worker_config.storage,
            ),
        )
