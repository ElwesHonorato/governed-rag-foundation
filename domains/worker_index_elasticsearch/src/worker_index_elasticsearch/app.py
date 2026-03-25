"""Installable entrypoint for the ``worker_index_elasticsearch`` domain."""

from pipeline_common.elasticsearch import (
    ChunkDocumentIndexPolicy,
)
from pipeline_common.gateways.elasticsearch import ElasticsearchIndexGateway
from pipeline_common.registry import DataHubDataJobKey, DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsBundle, SettingsProvider, SettingsRequest
from pipeline_common.startup import RuntimeContextFactory
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from worker_index_elasticsearch.services.worker_index_elasticsearch_service import WorkerIndexElasticsearchService
from worker_index_elasticsearch.startup.config_extractor import IndexElasticsearchConfigExtractor
from worker_index_elasticsearch.startup.contracts import RuntimeIndexElasticsearchJobConfig
from worker_index_elasticsearch.startup.service_factory import IndexElasticsearchServiceFactory


def main() -> int:
    worker_settings: SettingsBundle = SettingsProvider(
        SettingsRequest(datahub=True, storage=True, queue=True),
    ).bundle
    data_job_key: DataHubDataJobKey = DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(
        GovernedRagJobId.WORKER_INDEX_ELASTICSEARCH
    )
    runtime_context: WorkerRuntimeContext = RuntimeContextFactory(
        data_job_key=data_job_key,
        settings_bundle=worker_settings,
    ).build()
    runtime_job_config: RuntimeIndexElasticsearchJobConfig = IndexElasticsearchConfigExtractor().extract(
        runtime_context.job_properties,
    )
    index_policy = ChunkDocumentIndexPolicy()
    elasticsearch_gateway = ElasticsearchIndexGateway(
        url=runtime_job_config.elasticsearch_url,
        index_name=runtime_job_config.elasticsearch_index,
        index_policy=index_policy,
    )
    worker_service: WorkerIndexElasticsearchService = IndexElasticsearchServiceFactory(
        elasticsearch_gateway=elasticsearch_gateway,
    ).build(
        runtime_context,
        runtime_job_config,
    )
    worker_service.serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
