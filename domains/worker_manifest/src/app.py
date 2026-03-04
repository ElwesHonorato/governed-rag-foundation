"""worker_manifest entrypoint."""

from contracts.contracts import ManifestWorkerConfigContract
from registry import DataHubPipelineJobs
from pipeline_common.settings import SettingsProvider, SettingsRequest
from pipeline_common.startup import RuntimeContextFactory, WorkerRuntimeLauncher
from services.worker_manifest_service import WorkerManifestService
from startup.config_extractor import ManifestConfigExtractor
from startup.service_factory import ManifestServiceFactory


def run() -> None:
    """Start manifest worker."""
    settings = SettingsProvider(SettingsRequest(datahub=True, storage=True, queue=True, spark=False)).bundle
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_manifest"),
        settings_bundle=settings,
    )
    WorkerRuntimeLauncher[ManifestWorkerConfigContract, WorkerManifestService](
        runtime_factory=runtime_factory,
        config_extractor=ManifestConfigExtractor(),
        service_factory=ManifestServiceFactory(),
    ).start()


if __name__ == "__main__":
    run()
