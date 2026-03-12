"""worker_chunk_text entrypoint."""

from contracts.startup import RuntimeChunkJobConfig
from registry import DataHubDataJobKey, DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsBundle, SettingsProvider, SettingsRequest
from pipeline_common.startup import (
    RuntimeContextFactory,
)
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from services.worker_chunking_service import WorkerChunkingService
from startup.config_extractor import ChunkTextConfigExtractor
from startup.service_factory import ChunkTextServiceFactory


def run() -> None:
    """Start chunk_text worker."""
    settings: SettingsBundle = SettingsProvider(
        SettingsRequest(datahub=True, storage=True, queue=True),
    ).bundle

    data_job_key: DataHubDataJobKey = DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(
        GovernedRagJobId.WORKER_CHUNK_TEXT
    )
    runtime_context: WorkerRuntimeContext = RuntimeContextFactory(
        data_job_key=data_job_key,
        settings_bundle=settings,
    ).build()

    worker_config: RuntimeChunkJobConfig = ChunkTextConfigExtractor().extract(
        runtime_context.job_properties,
        env=runtime_context.env,
    )
    service: WorkerChunkingService = ChunkTextServiceFactory().build(runtime_context, worker_config)
    service.serve()


if __name__ == "__main__":
    run()
