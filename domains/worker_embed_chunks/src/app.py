"""worker_embed_chunks entrypoint."""

from registry import DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsBundle, SettingsProvider, SettingsRequest
from pipeline_common.startup import (
    RuntimeContextFactory,
    WorkerRuntimeLauncher,
)
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from startup.config_extractor import EmbedChunksConfigExtractor
from startup.service_factory import EmbedChunksServiceFactory


def run() -> None:
    """Start embed_chunks worker."""
    settings: SettingsBundle = SettingsProvider(
        SettingsRequest(datahub=True, storage=True, queue=True),
    ).bundle

    runtime_context: WorkerRuntimeContext = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(GovernedRagJobId.WORKER_EMBED_CHUNKS),
        settings_bundle=settings,
    ).build_runtime_context()

    WorkerRuntimeLauncher(
        runtime_context=runtime_context,
        config_extractor=EmbedChunksConfigExtractor(),
        service_factory=EmbedChunksServiceFactory(),
    ).start()


if __name__ == "__main__":
    run()
