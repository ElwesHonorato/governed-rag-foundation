"""Service graph assembly for worker_metrics startup."""

from contracts.metrics_worker_contracts import MetricsProcessingConfigContract, MetricsWorkerConfigContract
from pipeline_common.observability import Counters
from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from services.worker_metrics_service import WorkerMetricsService


class MetricsServiceFactory(WorkerServiceFactory[MetricsWorkerConfigContract, WorkerMetricsService]):
    """Build metrics service from runtime context and typed config."""

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: MetricsWorkerConfigContract,
    ) -> WorkerMetricsService:
        """Construct worker metrics service object graph."""
        return WorkerMetricsService(
            counters=Counters().for_worker("worker_metrics"),
            object_storage=runtime.object_storage_gateway,
            lineage=runtime.lineage_gateway,
            processing_config=MetricsProcessingConfigContract(
                poll_interval_seconds=worker_config.poll_interval_seconds,
                storage=worker_config.storage,
            ),
        )
