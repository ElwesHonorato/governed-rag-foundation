"""Service graph assembly for worker_chunk_text startup."""

from worker_chunk_text.chunking.resolver import ChunkingStagesResolver
from pipeline_common.gateways.object_storage import ManifestWriter
from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from worker_chunk_text.processor.chunk_text import ChunkTextProcessor
from worker_chunk_text.service.worker_chunking_service import WorkerChunkingService
from worker_chunk_text.startup.contracts import RuntimeChunkJobConfig


class ChunkTextServiceFactory(WorkerServiceFactory[RuntimeChunkJobConfig, WorkerChunkingService]):
    """Build chunk_text service from runtime context and typed config."""

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: RuntimeChunkJobConfig,
    ) -> WorkerChunkingService:
        """Construct the service graph for the chunk-text worker."""
        chunking_resolver: ChunkingStagesResolver = ChunkingStagesResolver()

        processor: ChunkTextProcessor = ChunkTextProcessor(
            object_storage=runtime.object_storage_gateway,
            queue_gateway=runtime.stage_queue_gateway,
            storage_bucket=worker_config.storage.bucket,
            output_prefix=worker_config.storage.output_prefix,
        )

        manifest_writer: ManifestWriter = ManifestWriter(
            object_storage=runtime.object_storage_gateway,
            storage_bucket=worker_config.storage.bucket,
            manifest_prefix=worker_config.storage.manifest_prefix,
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
