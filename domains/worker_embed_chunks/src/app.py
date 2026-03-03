"""worker_embed_chunks entrypoint."""

from contracts.contracts import EmbedChunksWorkerConfigContract
from registry import DataHubPipelineJobs
from pipeline_common.settings import SettingsProvider, SettingsRequest
from pipeline_common.startup import RuntimeContextFactory, WorkerRuntimeLauncher
from services.worker_embed_chunks_service import WorkerEmbedChunksService
from startup.config_extractor import EmbedChunksConfigExtractor
from startup.service_factory import EmbedChunksServiceFactory


def run() -> None:
    """Start embed_chunks worker."""
    settings = SettingsProvider(SettingsRequest(datahub=True, storage=True, queue=True, spark=True)).bundle
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_embed_chunks"),
        settings_bundle=settings,
    )
    WorkerRuntimeLauncher[EmbedChunksWorkerConfigContract, WorkerEmbedChunksService](
        runtime_factory=runtime_factory,
        config_extractor=EmbedChunksConfigExtractor(),
        service_factory=EmbedChunksServiceFactory(),
    ).start()


if __name__ == "__main__":
    run()
