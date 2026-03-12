"""Service graph assembly for worker_embed_chunks startup."""

from contracts.startup import RuntimeEmbedChunksJobConfig
from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from services.embed_chunks_processor import EmbedChunksProcessor
from services.worker_embed_chunks_service import WorkerEmbedChunksService


class EmbedChunksServiceFactory(WorkerServiceFactory[RuntimeEmbedChunksJobConfig, WorkerEmbedChunksService]):
    """Build embed_chunks service from runtime context and typed config."""

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: RuntimeEmbedChunksJobConfig,
    ) -> WorkerEmbedChunksService:
        """Construct worker embed_chunks service object graph."""
        processor: EmbedChunksProcessor = EmbedChunksProcessor(
            dimension=worker_config.dimension,
            object_storage=runtime.object_storage_gateway,
            storage_bucket=worker_config.storage.bucket,
            output_prefix=worker_config.storage.output_prefix,
        )
        return WorkerEmbedChunksService(
            stage_queue=runtime.stage_queue_gateway,
            object_storage=runtime.object_storage_gateway,
            lineage=runtime.lineage_gateway,
            poll_interval_seconds=worker_config.poll_interval_seconds,
            storage_bucket=worker_config.storage.bucket,
            processor=processor,
        )
