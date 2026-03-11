"""Service graph assembly for worker_metrics startup."""

from contracts.contracts import MetricsWorkerConfigContract
from pipeline_common.gateways.observability import Counters
from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from services.metrics_cycle_processor import MetricsCycleProcessor
from services.worker_metrics_service import WorkerMetricsService


class MetricsServiceFactory(WorkerServiceFactory[MetricsWorkerConfigContract, WorkerMetricsService]):
    """Build metrics service from runtime context and typed config."""

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: MetricsWorkerConfigContract,
    ) -> WorkerMetricsService:
        """Construct worker metrics service object graph."""
        processor: MetricsCycleProcessor = MetricsCycleProcessor()
        return WorkerMetricsService(
            counters=Counters().for_worker("worker_metrics"),
            object_storage=runtime.object_storage_gateway,
            lineage=runtime.lineage_gateway,
            poll_interval_seconds=worker_config.poll_interval_seconds,
            storage_bucket=worker_config.storage.bucket,
            processed_prefix=worker_config.storage.processed_prefix,
            chunks_prefix=worker_config.storage.chunks_prefix,
            embeddings_prefix=worker_config.storage.embeddings_prefix,
            indexes_prefix=worker_config.storage.indexes_prefix,
            processor=processor,
        )
