"""worker_metrics entrypoint."""

from registry import DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsBundle, SettingsProvider, SettingsRequest
from pipeline_common.startup import (
    RuntimeContextFactory,
    WorkerRuntimeLauncher,
)
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from startup.config_extractor import MetricsConfigExtractor
from startup.service_factory import MetricsServiceFactory


def run() -> None:
    """Start metrics worker."""
    settings: SettingsBundle = SettingsProvider(
        SettingsRequest(datahub=True, storage=True, queue=True),
    ).bundle

    runtime_context: WorkerRuntimeContext = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(GovernedRagJobId.WORKER_METRICS),
        settings_bundle=settings,
    ).build_runtime_context()

    WorkerRuntimeLauncher(
        runtime_context=runtime_context,
        config_extractor=MetricsConfigExtractor(),
        service_factory=MetricsServiceFactory(),
    ).start()


if __name__ == "__main__":
    run()
