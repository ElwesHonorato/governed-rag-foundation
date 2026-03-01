"""worker_index_weaviate entrypoint."""

from contracts.contracts import IndexWeaviateWorkerConfigContract
from pipeline_common.helpers.config import _required_env
from registry import DataHubPipelineJobs
from pipeline_common.settings import SettingsProvider, SettingsRequest
from pipeline_common.startup import RuntimeContextFactory, WorkerRuntimeLauncher
from services.worker_index_weaviate_service import WorkerIndexWeaviateService
from startup.config_extractor import IndexWeaviateConfigExtractor
from startup.service_factory import IndexWeaviateServiceFactory


def run() -> None:
    """Start index_weaviate worker."""
    settings = SettingsProvider(SettingsRequest(datahub=True, storage=True, queue=True)).bundle
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_index_weaviate"),
        settings_bundle=settings,
    )
    WorkerRuntimeLauncher[IndexWeaviateWorkerConfigContract, WorkerIndexWeaviateService](
        runtime_factory=runtime_factory,
        config_extractor=IndexWeaviateConfigExtractor(),
        service_factory=IndexWeaviateServiceFactory(weaviate_url=_required_env("WEAVIATE_URL")),
    ).start()


if __name__ == "__main__":
    run()
