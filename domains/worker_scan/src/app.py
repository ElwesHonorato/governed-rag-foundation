"""worker_scan entrypoint."""

from registry import DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsProvider, SettingsRequest
from pipeline_common.startup import (
    RuntimeContextFactory,
    WorkerRuntimeLauncher,
)
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from startup.config_extractor import ScanConfigExtractor
from startup.service_factory import ScanServiceFactory


def run() -> None:
    """Start scan worker."""
    settings = SettingsProvider(SettingsRequest(datahub=True, storage=True, queue=True)).bundle

    runtime_context: WorkerRuntimeContext = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(GovernedRagJobId.WORKER_SCAN),
        settings_bundle=settings,
    ).build_runtime_context()

    WorkerRuntimeLauncher(
        runtime_context=runtime_context,
        config_extractor=ScanConfigExtractor(),
        service_factory=ScanServiceFactory(),
    ).start()


if __name__ == "__main__":
    run()
