"""worker_metrics entrypoint."""

from contracts.contracts import MetricsWorkerConfigContract
from registry import DataHubPipelineJobs
from pipeline_common.settings import SettingsProvider, SettingsRequest
from pipeline_common.startup import RuntimeContextFactory, WorkerRuntimeLauncher
from services.worker_metrics_service import WorkerMetricsService
from startup.config_extractor import MetricsConfigExtractor
from startup.service_factory import MetricsServiceFactory


def run() -> None:
    """Start metrics worker."""
    settings = SettingsProvider(SettingsRequest(datahub=True, storage=True, queue=True)).bundle
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_metrics"),
        datahub_settings=settings.datahub,
        s3_settings=settings.storage,
        queue_settings=settings.queue,
    )
    WorkerRuntimeLauncher[MetricsWorkerConfigContract, WorkerMetricsService](
        runtime_factory=runtime_factory,
        config_extractor=MetricsConfigExtractor(),
        service_factory=MetricsServiceFactory(),
    ).start()


if __name__ == "__main__":
    run()
