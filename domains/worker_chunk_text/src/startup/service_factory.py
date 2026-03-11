"""Service graph assembly for worker_chunk_text startup."""

from contracts.contracts import ChunkTextStorageConfigContract, ChunkTextWorkerConfigContract
from configs.chunking_scaffold import ChunkingStagesResolver
from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from services.chunk_manifest_writer import ChunkManifestWriter
from services.chunk_text_processor import ChunkTextProcessor
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
        chunking_resolver: ChunkingStagesResolver = ChunkingStagesResolver()
        processor: ChunkTextProcessor = ChunkTextProcessor(
            object_storage=runtime.object_storage_gateway,
            storage_bucket=storage_config.bucket,
            output_prefix=storage_config.output_prefix,
        )
        manifest_writer: ChunkManifestWriter = ChunkManifestWriter(
            object_storage=runtime.object_storage_gateway,
            storage_bucket=storage_config.bucket,
            manifest_prefix=storage_config.manifest_prefix,
        )
        return WorkerChunkingService(
            queue_gateway=runtime.stage_queue_gateway,
            storage_gateway=runtime.object_storage_gateway,
            lineage_gateway=runtime.lineage_gateway,
            poll_interval_seconds=worker_config.poll_interval_seconds,
            chunking_resolver=chunking_resolver,
            processor=processor,
            manifest_writer=manifest_writer,
        )
