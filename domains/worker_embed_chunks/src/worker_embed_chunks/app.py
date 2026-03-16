"""Installable entrypoint for the ``worker_embed_chunks`` domain."""

from pipeline_common.registry import DataHubDataJobKey, DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsBundle, SettingsProvider, SettingsRequest
from pipeline_common.startup import RuntimeContextFactory
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from worker_embed_chunks.services.worker_embed_chunks_service import WorkerEmbedChunksService
from worker_embed_chunks.startup.embedding_composition import (
    EmbeddingCompositionFactory,
)
from worker_embed_chunks.startup.processor_factory import (
    EmbedChunksProcessorFactory,
)
from worker_embed_chunks.startup.config_extractor import EmbedChunksConfigExtractor
from worker_embed_chunks.startup.contracts import RuntimeEmbedChunksJobConfig
from worker_embed_chunks.startup.service_factory import EmbedChunksServiceFactory


def main() -> int:
    worker_embed_chunks_settings: SettingsBundle = SettingsProvider(
        SettingsRequest(datahub=True, storage=True, queue=True),
    ).bundle
    worker_embed_chunks_data_job_key: DataHubDataJobKey = DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(
        GovernedRagJobId.WORKER_EMBED_CHUNKS
    )
    worker_embed_chunks_runtime_context: WorkerRuntimeContext = RuntimeContextFactory(
        data_job_key=worker_embed_chunks_data_job_key,
        settings_bundle=worker_embed_chunks_settings,
    ).build()
    worker_embed_chunks_runtime_job_config: RuntimeEmbedChunksJobConfig = (
        EmbedChunksConfigExtractor().extract(
            worker_embed_chunks_runtime_context.job_properties,
            env=worker_embed_chunks_runtime_context.env,
        )
    )
    worker_embed_chunks_service: WorkerEmbedChunksService = EmbedChunksServiceFactory(
        embedding_composition_factory=EmbeddingCompositionFactory(),
        processor_factory=EmbedChunksProcessorFactory(),
    ).build(
        worker_embed_chunks_runtime_context,
        worker_embed_chunks_runtime_job_config,
    )
    worker_embed_chunks_service.serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
