"""Service graph assembly for worker_index_weaviate startup."""

from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from worker_index_weaviate.services.index_flow import IndexStatusWriter
from worker_index_weaviate.services.index_weaviate_processor import IndexWeaviateProcessor
from worker_index_weaviate.services.weaviate_gateway import ensure_schema
from worker_index_weaviate.services.worker_index_weaviate_service import WorkerIndexWeaviateService
from worker_index_weaviate.startup.contracts import RuntimeIndexWeaviateJobConfig


class IndexWeaviateServiceFactory(WorkerServiceFactory[RuntimeIndexWeaviateJobConfig, WorkerIndexWeaviateService]):
    """Build index_weaviate service from runtime context and typed config."""

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: RuntimeIndexWeaviateJobConfig,
    ) -> WorkerIndexWeaviateService:
        """Construct worker index_weaviate service object graph."""
        ensure_schema(worker_config.weaviate_url)
        status_writer: IndexStatusWriter = IndexStatusWriter(
            object_storage=runtime.object_storage_gateway,
            storage_bucket=worker_config.storage.bucket,
        )
        processor: IndexWeaviateProcessor = IndexWeaviateProcessor(
            object_storage=runtime.object_storage_gateway,
            status_writer=status_writer,
            storage_bucket=worker_config.storage.bucket,
            output_prefix=worker_config.storage.output_prefix,
            weaviate_url=worker_config.weaviate_url,
        )
        return WorkerIndexWeaviateService(
            stage_queue=runtime.stage_queue_gateway,
            object_storage=runtime.object_storage_gateway,
            lineage=runtime.lineage_gateway,
            poll_interval_seconds=worker_config.poll_interval_seconds,
            processor=processor,
        )
