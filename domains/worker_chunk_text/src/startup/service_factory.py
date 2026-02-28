"""Service graph assembly for worker_chunk_text startup."""

from configs.chunk_text_worker_config import (
    ChunkTextProcessingConfigContract,
    ChunkTextStorageConfigContract,
    ChunkTextWorkerConfig,
)
from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from services.worker_chunk_text_service import WorkerChunkTextService


class ChunkTextServiceFactory(WorkerServiceFactory[ChunkTextWorkerConfig, WorkerChunkTextService]):
    """Build chunk_text service from runtime context and typed config."""

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: ChunkTextWorkerConfig,
    ) -> WorkerChunkTextService:
        """Construct worker chunk_text service object graph."""
        return WorkerChunkTextService(
            stage_queue=runtime.stage_queue_gateway,
            object_storage=runtime.object_storage_gateway,
            lineage=runtime.lineage_gateway,
            processing_config=ChunkTextProcessingConfigContract(
                poll_interval_seconds=worker_config.poll_interval_seconds,
                queue=worker_config.queue_config,
                storage=ChunkTextStorageConfigContract(
                    bucket=worker_config.bucket,
                    input_prefix=worker_config.input_prefix,
                    output_prefix=worker_config.output_prefix,
                ),
            ),
        )
