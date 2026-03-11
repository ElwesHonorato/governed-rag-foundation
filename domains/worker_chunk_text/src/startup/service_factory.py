"""Service graph assembly for worker_chunk_text startup."""

from contracts.contracts import ChunkTextStorageConfigContract, ChunkTextWorkerConfigContract
from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from services.worker_chunking_service import WorkerChunkingService
from startup.storage_config_builder import EnvStorageConfigBuilder


class ChunkTextServiceFactory(WorkerServiceFactory[ChunkTextWorkerConfigContract, WorkerChunkingService]):
    """Build chunk_text service from runtime context and typed config."""

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: ChunkTextWorkerConfigContract,
    ) -> WorkerChunkingService:
        """Construct worker chunk_text service object graph."""
        storage_config: ChunkTextStorageConfigContract = EnvStorageConfigBuilder(
            env=runtime.env,
            storage_config=worker_config.storage,
        ).build()
        return WorkerChunkingService(
            queue_gateway=runtime.stage_queue_gateway,
            storage_gateway=runtime.object_storage_gateway,
            lineage_gateway=runtime.lineage_gateway,
            poll_interval_seconds=worker_config.poll_interval_seconds,
            storage_config=storage_config,
        )
