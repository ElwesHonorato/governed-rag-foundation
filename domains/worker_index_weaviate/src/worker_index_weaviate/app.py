"""Installable entrypoint for the ``worker_index_weaviate`` domain."""

from pipeline_common.registry import DataHubDataJobKey, DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsBundle, SettingsProvider, SettingsRequest
from pipeline_common.startup import RuntimeContextFactory
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from worker_index_weaviate.services.worker_index_weaviate_service import WorkerIndexWeaviateService
from worker_index_weaviate.startup.config_extractor import IndexWeaviateConfigExtractor
from worker_index_weaviate.startup.contracts import RuntimeIndexWeaviateJobConfig
from worker_index_weaviate.startup.service_factory import IndexWeaviateServiceFactory


def main() -> int:
    worker_index_weaviate_settings: SettingsBundle = SettingsProvider(
        SettingsRequest(datahub=True, storage=True, queue=True),
    ).bundle
    worker_index_weaviate_data_job_key: DataHubDataJobKey = DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(
        GovernedRagJobId.WORKER_INDEX_WEAVIATE
    )
    worker_index_weaviate_runtime_context: WorkerRuntimeContext = RuntimeContextFactory(
        data_job_key=worker_index_weaviate_data_job_key,
        settings_bundle=worker_index_weaviate_settings,
    ).build()
    worker_index_weaviate_runtime_job_config: RuntimeIndexWeaviateJobConfig = (
        IndexWeaviateConfigExtractor().extract(
            worker_index_weaviate_runtime_context.job_properties,
            env=worker_index_weaviate_runtime_context.env,
        )
    )
    worker_index_weaviate_service: WorkerIndexWeaviateService = IndexWeaviateServiceFactory().build(
        worker_index_weaviate_runtime_context,
        worker_index_weaviate_runtime_job_config,
    )
    worker_index_weaviate_service.serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
