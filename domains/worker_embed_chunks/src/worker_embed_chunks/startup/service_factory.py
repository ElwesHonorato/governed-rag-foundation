"""Service graph assembly for worker_embed_chunks startup."""

from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from worker_embed_chunks.services.worker_embed_chunks_service import WorkerEmbedChunksService
from worker_embed_chunks.startup.embedding_composition import (
    EmbeddingCompositionFactory,
)
from worker_embed_chunks.startup.contracts import RuntimeEmbedChunksJobConfig
from worker_embed_chunks.startup.processor_factory import (
    EmbedChunksProcessorFactory,
)


class EmbedChunksServiceFactory(WorkerServiceFactory[RuntimeEmbedChunksJobConfig, WorkerEmbedChunksService]):
    """Build embed_chunks service from runtime context and typed config."""

    def __init__(
        self,
        *,
        embedding_composition_factory: EmbeddingCompositionFactory,
        processor_factory: EmbedChunksProcessorFactory,
    ) -> None:
        self._embedding_composition_factory = embedding_composition_factory
        self._processor_factory = processor_factory

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: RuntimeEmbedChunksJobConfig,
    ) -> WorkerEmbedChunksService:
        """Construct worker embed_chunks service object graph."""
        embedding = self._embedding_composition_factory.build(worker_config.dimension)
        processor = self._processor_factory.build(
            embedding=embedding,
            object_storage=runtime.object_storage_gateway,
            worker_config=worker_config,
        )
        return WorkerEmbedChunksService(
            stage_queue=runtime.stage_queue_gateway,
            object_storage=runtime.object_storage_gateway,
            lineage=runtime.lineage_gateway,
            poll_interval_seconds=worker_config.poll_interval_seconds,
            processor=processor,
        )
