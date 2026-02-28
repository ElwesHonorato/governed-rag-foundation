"""worker_embed_chunks entrypoint."""

from contracts.contracts import EmbedChunksWorkerConfigContract
from registry import DataHubPipelineJobs
from pipeline_common.gateways.lineage.settings import DataHubSettings
from pipeline_common.gateways.queue.settings import QueueRuntimeSettings
from pipeline_common.gateways.object_storage.settings import S3StorageSettings
from pipeline_common.startup import RuntimeContextFactory, WorkerRuntimeLauncher
from services.worker_embed_chunks_service import WorkerEmbedChunksService
from startup.config_extractor import EmbedChunksConfigExtractor
from startup.service_factory import EmbedChunksServiceFactory


def run() -> None:
    """Start embed_chunks worker."""
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_embed_chunks"),
        datahub_settings=DataHubSettings.from_env(),
        s3_settings=S3StorageSettings.from_env(),
        queue_settings=QueueRuntimeSettings.from_env(),
    )
    WorkerRuntimeLauncher[EmbedChunksWorkerConfigContract, WorkerEmbedChunksService](
        runtime_factory=runtime_factory,
        config_extractor=EmbedChunksConfigExtractor(),
        service_factory=EmbedChunksServiceFactory(),
    ).start()


if __name__ == "__main__":
    run()
