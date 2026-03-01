"""worker_chunk_text entrypoint."""

from contracts.contracts import ChunkTextWorkerConfigContract
from registry import DataHubPipelineJobs
from pipeline_common.settings import SettingsProvider, SettingsRequest
from pipeline_common.startup import RuntimeContextFactory, WorkerRuntimeLauncher
from services.worker_chunk_text_service import WorkerChunkTextService
from startup.config_extractor import ChunkTextConfigExtractor
from startup.service_factory import ChunkTextServiceFactory


def run() -> None:
    """Start chunk_text worker."""
    settings = SettingsProvider(SettingsRequest(datahub=True, storage=True, queue=True)).bundle
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_chunk_text"),
        settings_bundle=settings,
    )
    WorkerRuntimeLauncher[ChunkTextWorkerConfigContract, WorkerChunkTextService](
        runtime_factory=runtime_factory,
        config_extractor=ChunkTextConfigExtractor(),
        service_factory=ChunkTextServiceFactory(),
    ).start()


if __name__ == "__main__":
    run()
