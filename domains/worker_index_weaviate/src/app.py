"""worker_index_weaviate entrypoint."""

from contracts.startup import RuntimeIndexWeaviateJobConfig
from pipeline_common.helpers.config import _required_env
from registry import DataHubDataJobKey, DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsBundle, SettingsProvider, SettingsRequest
from pipeline_common.startup import (
    RuntimeContextFactory,
)
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from services.worker_index_weaviate_service import WorkerIndexWeaviateService
from startup.config_extractor import IndexWeaviateConfigExtractor
from startup.service_factory import IndexWeaviateServiceFactory


def run() -> None:
    """Start index_weaviate worker."""
    settings: SettingsBundle = SettingsProvider(
        SettingsRequest(datahub=True, storage=True, queue=True),
    ).bundle

    data_job_key: DataHubDataJobKey = DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(
        GovernedRagJobId.WORKER_INDEX_WEAVIATE
    )
    runtime_context: WorkerRuntimeContext = RuntimeContextFactory(
        data_job_key=data_job_key,
        settings_bundle=settings,
    ).build()

    runtime_job_config: RuntimeIndexWeaviateJobConfig = IndexWeaviateConfigExtractor().extract(
        runtime_context.job_properties
    )
    service: WorkerIndexWeaviateService = IndexWeaviateServiceFactory(
        weaviate_url=_required_env("WEAVIATE_URL"),
    ).build(runtime_context, runtime_job_config)
    service.serve()


if __name__ == "__main__":
    run()
