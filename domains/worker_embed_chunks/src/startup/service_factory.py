"""Service graph assembly for worker_embed_chunks startup."""

from contracts.contracts import EmbedChunksProcessingConfigContract, EmbedChunksWorkerConfigContract
from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from services.worker_embed_chunks_service import WorkerEmbedChunksService


class EmbedChunksServiceFactory(WorkerServiceFactory[EmbedChunksWorkerConfigContract, WorkerEmbedChunksService]):
    """Build embed_chunks service from runtime context and typed config."""

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: EmbedChunksWorkerConfigContract,
    ) -> WorkerEmbedChunksService:
        """Construct worker embed_chunks service object graph."""
        return WorkerEmbedChunksService(
            stage_queue=runtime.stage_queue_gateway,
            object_storage=runtime.object_storage_gateway,
            lineage=runtime.lineage_gateway,
            processing_config=EmbedChunksProcessingConfigContract(
                poll_interval_seconds=worker_config.poll_interval_seconds,
                queue=worker_config.queue_config,
                storage=worker_config.storage,
            ),
            dimension=worker_config.dimension,
        )
