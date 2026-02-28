"""worker_manifest entrypoint."""

from contracts.contracts import ManifestWorkerConfigContract
from registry import DataHubPipelineJobs
from pipeline_common.gateways.lineage.settings import DataHubSettings
from pipeline_common.gateways.queue.settings import QueueRuntimeSettings
from pipeline_common.gateways.object_storage.settings import S3StorageSettings
from pipeline_common.startup import RuntimeContextFactory, WorkerRuntimeLauncher
from services.worker_manifest_service import WorkerManifestService
from startup.config_extractor import ManifestConfigExtractor
from startup.service_factory import ManifestServiceFactory


def run() -> None:
    """Start manifest worker."""
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_manifest"),
        datahub_settings=DataHubSettings.from_env(),
        s3_settings=S3StorageSettings.from_env(),
        queue_settings=QueueRuntimeSettings.from_env(),
    )
    WorkerRuntimeLauncher[ManifestWorkerConfigContract, WorkerManifestService](
        runtime_factory=runtime_factory,
        config_extractor=ManifestConfigExtractor(),
        service_factory=ManifestServiceFactory(),
    ).start()


if __name__ == "__main__":
    run()
