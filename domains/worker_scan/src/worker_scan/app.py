"""Installable entrypoint for the ``worker_scan`` domain."""

from pipeline_common.registry import DataHubDataJobKey, DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsBundle, SettingsProvider, SettingsRequest
from pipeline_common.startup import RuntimeContextFactory
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from worker_scan.services.worker_scan_service import WorkerScanService
from worker_scan.startup.config_extractor import ScanConfigExtractor
from worker_scan.startup.contracts import RuntimeScanJobConfig
from worker_scan.startup.service_factory import ScanServiceFactory


def main() -> int:
    worker_scan_settings: SettingsBundle = SettingsProvider(
        SettingsRequest(datahub=True, storage=True, queue=True),
    ).bundle
    worker_scan_data_job_key: DataHubDataJobKey = DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(
        GovernedRagJobId.WORKER_SCAN
    )
    worker_scan_runtime_context: WorkerRuntimeContext = RuntimeContextFactory(
        data_job_key=worker_scan_data_job_key,
        settings_bundle=worker_scan_settings,
    ).build()
    worker_scan_runtime_job_config: RuntimeScanJobConfig = ScanConfigExtractor().extract(
        worker_scan_runtime_context.job_properties,
        env=worker_scan_runtime_context.env,
    )
    worker_scan_service: WorkerScanService = ScanServiceFactory().build(
        worker_scan_runtime_context,
        worker_scan_runtime_job_config,
    )
    worker_scan_service.serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
