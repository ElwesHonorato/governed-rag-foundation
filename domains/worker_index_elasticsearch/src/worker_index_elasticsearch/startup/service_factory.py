"""Service graph assembly for worker_index_elasticsearch startup."""

from pipeline_common.gateways.elasticsearch import ElasticsearchGateway
from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from worker_index_elasticsearch.services.index_elasticsearch_processor import IndexElasticsearchProcessor
from worker_index_elasticsearch.services.worker_index_elasticsearch_service import WorkerIndexElasticsearchService
from worker_index_elasticsearch.startup.contracts import RuntimeIndexElasticsearchJobConfig


class IndexElasticsearchServiceFactory(
    WorkerServiceFactory[RuntimeIndexElasticsearchJobConfig, WorkerIndexElasticsearchService]
):
    """Build worker_index_elasticsearch service from runtime context and typed config."""

    def __init__(self, *, elasticsearch_gateway: ElasticsearchGateway) -> None:
        """Store Elasticsearch runtime dependency."""
        self._elasticsearch_gateway = elasticsearch_gateway

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: RuntimeIndexElasticsearchJobConfig,
    ) -> WorkerIndexElasticsearchService:
        """Construct worker index_elasticsearch service object graph."""
        processor = IndexElasticsearchProcessor(
            elasticsearch_gateway=self._elasticsearch_gateway,
        )
        return WorkerIndexElasticsearchService(
            stage_queue=runtime.stage_queue_gateway,
            object_storage=runtime.object_storage_gateway,
            lineage=runtime.lineage_gateway,
            poll_interval_seconds=worker_config.poll_interval_seconds,
            processor=processor,
        )
