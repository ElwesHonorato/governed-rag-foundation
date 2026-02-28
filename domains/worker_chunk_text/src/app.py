"""worker_chunk_text entrypoint."""

from configs.chunk_text_worker_config import ChunkTextWorkerConfig
from pipeline_common.lineage.pipeline import DataHubPipelineJobs
from pipeline_common.settings import DataHubSettings, QueueRuntimeSettings, S3StorageSettings
from pipeline_common.startup import RuntimeContextFactory, WorkerRuntimeLauncher
from services.worker_chunk_text_service import WorkerChunkTextService
from startup.config_extractor import ChunkTextConfigExtractor
from startup.service_factory import ChunkTextServiceFactory


def run() -> None:
    """Start chunk_text worker."""
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_chunk_text"),
        datahub_settings=DataHubSettings.from_env(),
        s3_settings=S3StorageSettings.from_env(),
        queue_settings=QueueRuntimeSettings.from_env(),
    )
    WorkerRuntimeLauncher[ChunkTextWorkerConfig, WorkerChunkTextService](
        runtime_factory=runtime_factory,
        config_extractor=ChunkTextConfigExtractor(),
        service_factory=ChunkTextServiceFactory(),
    ).start()


if __name__ == "__main__":
    run()
