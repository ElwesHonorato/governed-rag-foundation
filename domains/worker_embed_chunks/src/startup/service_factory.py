"""Service graph assembly for worker_embed_chunks startup."""

from contracts.embed_chunks_worker_contracts import (
    EmbedChunksProcessingConfigContract,
    EmbedChunksStorageConfigContract,
    EmbedChunksWorkerConfigContract,
)
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
                storage=EmbedChunksStorageConfigContract(
                    bucket=worker_config.bucket,
                    input_prefix=worker_config.input_prefix,
                    output_prefix=worker_config.output_prefix,
                ),
            ),
            dimension=worker_config.dimension,
        )
