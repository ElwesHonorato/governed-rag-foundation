"""worker_metrics entrypoint."""

from contracts.metrics_worker_contracts import MetricsWorkerConfigContract
from pipeline_common.lineage.pipeline import DataHubPipelineJobs
from pipeline_common.settings import DataHubSettings, QueueRuntimeSettings, S3StorageSettings
from pipeline_common.startup import RuntimeContextFactory, WorkerRuntimeLauncher
from services.worker_metrics_service import WorkerMetricsService
from startup.config_extractor import MetricsConfigExtractor
from startup.service_factory import MetricsServiceFactory


def run() -> None:
    """Start metrics worker."""
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_metrics"),
        datahub_settings=DataHubSettings.from_env(),
        s3_settings=S3StorageSettings.from_env(),
        queue_settings=QueueRuntimeSettings.from_env(),
    )
    WorkerRuntimeLauncher[MetricsWorkerConfigContract, WorkerMetricsService](
        runtime_factory=runtime_factory,
        config_extractor=MetricsConfigExtractor(),
        service_factory=MetricsServiceFactory(),
    ).start()


if __name__ == "__main__":
    run()
