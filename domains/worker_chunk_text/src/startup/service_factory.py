"""Service graph assembly for worker_chunk_text startup."""

from contracts.contracts import ChunkTextWorkerConfigContract
from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from services.worker_chunk_text_service import WorkerChunkTextService


class ChunkTextServiceFactory(WorkerServiceFactory[ChunkTextWorkerConfigContract, WorkerChunkTextService]):
    """Build chunk_text service from runtime context and typed config."""

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: ChunkTextWorkerConfigContract,
    ) -> WorkerChunkTextService:
        """Construct worker chunk_text service object graph."""
        return WorkerChunkTextService(
            queue_gateway=runtime.stage_queue_gateway,
            storage_gateway=runtime.object_storage_gateway,
            lineage_gateway=runtime.lineage_gateway,
            env=runtime.env,
            poll_interval_seconds=worker_config.poll_interval_seconds,
            storage_config=worker_config.storage,
        )
