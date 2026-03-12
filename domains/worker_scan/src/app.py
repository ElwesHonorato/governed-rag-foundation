"""worker_scan entrypoint."""

from contracts.startup import RuntimeScanJobConfig
from registry import DataHubDataJobKey, DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsBundle, SettingsProvider, SettingsRequest
from pipeline_common.startup import (
    RuntimeContextFactory,
)
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from services.worker_scan_service import WorkerScanService
from startup.config_extractor import ScanConfigExtractor
from startup.service_factory import ScanServiceFactory


def run() -> None:
    """Start scan worker."""
    settings: SettingsBundle = SettingsProvider(
        SettingsRequest(datahub=True, storage=True, queue=True),
    ).bundle

    data_job_key: DataHubDataJobKey = DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(
        GovernedRagJobId.WORKER_SCAN
    )
    runtime_context: WorkerRuntimeContext = RuntimeContextFactory(
        data_job_key=data_job_key,
        settings_bundle=settings,
    ).build()

    runtime_job_config: RuntimeScanJobConfig = ScanConfigExtractor().extract(runtime_context.job_properties)
    service: WorkerScanService = ScanServiceFactory().build(runtime_context, runtime_job_config)
    service.serve()


if __name__ == "__main__":
    run()
