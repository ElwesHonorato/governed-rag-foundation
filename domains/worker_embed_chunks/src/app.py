"""worker_embed_chunks entrypoint."""

from contracts.startup import RuntimeEmbedChunksJobConfig
from registry import DataHubDataJobKey, DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsBundle, SettingsProvider, SettingsRequest
from pipeline_common.startup import (
    RuntimeContextFactory,
)
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from services.worker_embed_chunks_service import WorkerEmbedChunksService
from startup.config_extractor import EmbedChunksConfigExtractor
from startup.service_factory import EmbedChunksServiceFactory


def run() -> None:
    """Start embed_chunks worker."""
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
        runtime_context.job_properties
    )
    service: WorkerEmbedChunksService = EmbedChunksServiceFactory().build(runtime_context, runtime_job_config)
    service.serve()


if __name__ == "__main__":
    run()
