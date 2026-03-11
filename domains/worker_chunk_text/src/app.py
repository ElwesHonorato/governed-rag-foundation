"""worker_chunk_text entrypoint."""

from contracts.contracts import ChunkTextWorkerConfigContract
from registry import DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsProvider, SettingsRequest
from pipeline_common.startup import RuntimeContextFactory, WorkerRuntimeLauncher
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from services.worker_chunk_text_service import WorkerChunkTextService
from startup.config_extractor import ChunkTextConfigExtractor
from startup.service_factory import ChunkTextServiceFactory


def run() -> None:
    """Start chunk_text worker."""
    settings = SettingsProvider(SettingsRequest(datahub=True, storage=True, queue=True)).bundle
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(GovernedRagJobId.WORKER_CHUNK_TEXT),
        settings_bundle=settings,
    )
    runtime_context: WorkerRuntimeContext = runtime_factory.build_runtime_context()
    WorkerRuntimeLauncher[ChunkTextWorkerConfigContract, WorkerChunkTextService](
        runtime_context=runtime_context,
        config_extractor=ChunkTextConfigExtractor(),
        service_factory=ChunkTextServiceFactory(),
    ).start()


if __name__ == "__main__":
    run()
