"""Service graph assembly for worker_manifest startup."""

from contracts.contracts import ManifestWorkerConfigContract
from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from services.manifest_cycle_processor import ManifestCycleProcessor
from services.worker_manifest_service import WorkerManifestService


class ManifestServiceFactory(WorkerServiceFactory[ManifestWorkerConfigContract, WorkerManifestService]):
    """Build manifest service from runtime context and typed config."""

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: ManifestWorkerConfigContract,
    ) -> WorkerManifestService:
        """Construct worker manifest service object graph."""
        processor: ManifestCycleProcessor = ManifestCycleProcessor(
            processed_prefix=worker_config.storage.processed_prefix,
            manifest_prefix=worker_config.storage.manifest_prefix,
        )
        return WorkerManifestService(
            object_storage=runtime.object_storage_gateway,
            lineage=runtime.lineage_gateway,
            poll_interval_seconds=worker_config.poll_interval_seconds,
            storage_bucket=worker_config.storage.bucket,
            chunks_prefix=worker_config.storage.chunks_prefix,
            embeddings_prefix=worker_config.storage.embeddings_prefix,
            indexes_prefix=worker_config.storage.indexes_prefix,
            processed_prefix=worker_config.storage.processed_prefix,
            processor=processor,
        )
