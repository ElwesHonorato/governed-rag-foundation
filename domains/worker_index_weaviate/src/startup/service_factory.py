"""Service graph assembly for worker_index_weaviate startup."""

from contracts.index_weaviate_worker_contracts import IndexWeaviateProcessingConfigContract, IndexWeaviateWorkerConfigContract
from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from pipeline_common.weaviate import ensure_schema
from services.worker_index_weaviate_service import WorkerIndexWeaviateService


class IndexWeaviateServiceFactory(WorkerServiceFactory[IndexWeaviateWorkerConfigContract, WorkerIndexWeaviateService]):
    """Build index_weaviate service from runtime context and typed config."""

    def __init__(self, *, weaviate_url: str) -> None:
        self._weaviate_url = weaviate_url

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: IndexWeaviateWorkerConfigContract,
    ) -> WorkerIndexWeaviateService:
        """Construct worker index_weaviate service object graph."""
        ensure_schema(self._weaviate_url)
        return WorkerIndexWeaviateService(
            stage_queue=runtime.stage_queue_gateway,
            object_storage=runtime.object_storage_gateway,
            lineage=runtime.lineage_gateway,
            processing_config=IndexWeaviateProcessingConfigContract(
                poll_interval_seconds=worker_config.poll_interval_seconds,
                queue=worker_config.queue_config,
                storage=worker_config.storage,
            ),
            weaviate_url=self._weaviate_url,
        )
