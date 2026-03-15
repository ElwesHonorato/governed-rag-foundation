"""Installable entrypoint for the ``worker_embed_chunks`` domain."""

from pipeline_common.registry import DataHubDataJobKey, DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsBundle, SettingsProvider, SettingsRequest
from pipeline_common.startup import RuntimeContextFactory
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from worker_embed_chunks.services.worker_embed_chunks_service import WorkerEmbedChunksService
from worker_embed_chunks.startup.config_extractor import EmbedChunksConfigExtractor
from worker_embed_chunks.startup.contracts import RuntimeEmbedChunksJobConfig
from worker_embed_chunks.startup.service_factory import EmbedChunksServiceFactory


def run() -> None:
    settings: SettingsBundle = SettingsProvider(
        SettingsRequest(datahub=True, storage=True, queue=True),
    ).bundle
    data_job_key: DataHubDataJobKey = DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(
        GovernedRagJobId.WORKER_EMBED_CHUNKS
    )
    runtime_context: WorkerRuntimeContext = RuntimeContextFactory(
        data_job_key=data_job_key,
        settings_bundle=settings,
    ).build()
    runtime_job_config: RuntimeEmbedChunksJobConfig = EmbedChunksConfigExtractor().extract(
        runtime_context.job_properties,
        env=runtime_context.env,
    )
    service: WorkerEmbedChunksService = EmbedChunksServiceFactory().build(runtime_context, runtime_job_config)
    service.serve()


def main() -> int:
    run()
    return 0
