"""worker_scan entrypoint."""

from registry import DataHubPipelineJobs
from pipeline_common.settings import DataHubSettings, QueueRuntimeSettings, S3StorageSettings
from pipeline_common.startup import (
    RuntimeContextFactory,
    WorkerRuntimeLauncher,
)
from contracts.contracts import ScanWorkerConfigContract
from services.worker_scan_service import WorkerScanService
from startup.config_extractor import ScanConfigExtractor
from startup.service_factory import ScanServiceFactory


def run() -> None:
    """Start scan worker."""
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_scan"),
        datahub_settings=DataHubSettings.from_env(),
        s3_settings=S3StorageSettings.from_env(),
        queue_settings=QueueRuntimeSettings.from_env(),
    )
    WorkerRuntimeLauncher[ScanWorkerConfigContract, WorkerScanService](
        runtime_factory=runtime_factory,
        config_extractor=ScanConfigExtractor(),
        service_factory=ScanServiceFactory(),
    ).start()


if __name__ == "__main__":
    run()
