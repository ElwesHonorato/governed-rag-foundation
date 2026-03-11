"""worker_index_weaviate entrypoint."""

from pipeline_common.helpers.config import _required_env
from registry import DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsProvider, SettingsRequest
from pipeline_common.startup import RuntimeContextFactory, WorkerRuntimeLauncher
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from startup.config_extractor import IndexWeaviateConfigExtractor
from startup.service_factory import IndexWeaviateServiceFactory


def run() -> None:
    """Start index_weaviate worker."""
    settings = SettingsProvider(SettingsRequest(datahub=True, storage=True, queue=True)).bundle
    runtime_context: WorkerRuntimeContext = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(GovernedRagJobId.WORKER_INDEX_WEAVIATE),
        settings_bundle=settings,
    ).build_runtime_context()
    WorkerRuntimeLauncher(
        runtime_context=runtime_context,
        config_extractor=IndexWeaviateConfigExtractor(),
        service_factory=IndexWeaviateServiceFactory(weaviate_url=_required_env("WEAVIATE_URL")),
    ).start()


if __name__ == "__main__":
    run()
