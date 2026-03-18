"""Service graph assembly for worker_embed_chunks startup."""

from ai_infra.retrieval.deterministic_hash_embedder import (
    DeterministicHashEmbedder,
)
from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from worker_embed_chunks.services.worker_embed_chunks_service import WorkerEmbedChunksService
from worker_embed_chunks.startup.contracts import RuntimeEmbedChunksJobConfig
from worker_embed_chunks.startup.processor_factory import (
    EmbedChunksProcessorFactory,
)


class EmbedChunksServiceFactory(WorkerServiceFactory[RuntimeEmbedChunksJobConfig, WorkerEmbedChunksService]):
    """Build embed_chunks service from runtime context and typed config."""

    def __init__(
        self,
        *,
        processor_factory: EmbedChunksProcessorFactory,
    ) -> None:
        self._processor_factory = processor_factory

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: RuntimeEmbedChunksJobConfig,
    ) -> WorkerEmbedChunksService:
        """Construct worker embed_chunks service object graph."""
        embedder = DeterministicHashEmbedder(worker_config.dimension)
        processor = self._processor_factory.build(
            embedder=embedder,
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
