import logging
import time

from contracts.contracts import MetricsProcessingConfigContract
from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.observability import Counters
from pipeline_common.startup.contracts import WorkerService
from services.metrics_cycle_processor import MetricsCycleProcessor

logger = logging.getLogger(__name__)


class WorkerMetricsService(WorkerService):
    """Emit pipeline stage counters on a fixed interval."""
    def __init__(
        self,
        *,
        counters: Counters,
        object_storage: ObjectStorageGateway,
        lineage: LineageRuntimeGateway,
        processing_config: MetricsProcessingConfigContract,
    ) -> None:
        """Initialize instance state and dependencies."""
        self.counters = counters
        self.object_storage = object_storage
        self.lineage = lineage
        self._initialize_runtime_config(processing_config)
        self.processor = MetricsCycleProcessor()

    def serve(self) -> None:
        """Run the worker loop indefinitely."""
        while True:
            self._run_metrics_iteration()

    def _run_metrics_iteration(self) -> None:
        try:
            self._run_metrics_cycle()
        except Exception as exc:
            self._handle_metrics_cycle_failure(exc)
        finally:
            self._sleep_until_next_cycle()

    def _run_metrics_cycle(self) -> None:
        self.lineage.start_run()
        self.lineage.add_input(name=f"{self.storage_bucket}/{self.processed_prefix}", platform=DatasetPlatform.S3)
        self.lineage.add_input(name=f"{self.storage_bucket}/{self.chunks_prefix}", platform=DatasetPlatform.S3)
        self.lineage.add_input(name=f"{self.storage_bucket}/{self.embeddings_prefix}", platform=DatasetPlatform.S3)
        self.lineage.add_input(name=f"{self.storage_bucket}/{self.indexes_prefix}", platform=DatasetPlatform.S3)

        processed_keys = self.object_storage.list_keys(self.storage_bucket, self.processed_prefix)
        chunk_keys = self.object_storage.list_keys(self.storage_bucket, self.chunks_prefix)
        embedding_keys = self.object_storage.list_keys(self.storage_bucket, self.embeddings_prefix)
        indexed_keys = self.object_storage.list_keys(self.storage_bucket, self.indexes_prefix)
        counts = self.processor.build_counts(
            processed_keys=processed_keys,
            chunk_keys=chunk_keys,
            embedding_keys=embedding_keys,
            indexed_keys=indexed_keys,
        )

        self.counters.files_processed = counts["files_processed"]
        self.counters.chunks_created = counts["chunks_created"]
        self.counters.embedding_artifacts = counts["embedding_artifacts"]
        self.counters.index_upserts = counts["index_upserts"]
        self.counters.emit()
        self.lineage.complete_run()

    def _handle_metrics_cycle_failure(self, exc: Exception) -> None:
        self.lineage.fail_run(error_message=str(exc))
        logger.exception("Failed collecting pipeline metrics")

    def _sleep_until_next_cycle(self) -> None:
        time.sleep(self.poll_interval_seconds)

    def _initialize_runtime_config(self, processing_config: MetricsProcessingConfigContract) -> None:
        """Internal helper for initialize runtime config."""
        self.poll_interval_seconds = processing_config.poll_interval_seconds
        self.storage_bucket = processing_config.storage.bucket
        self.processed_prefix = processing_config.storage.processed_prefix
        self.chunks_prefix = processing_config.storage.chunks_prefix
        self.embeddings_prefix = processing_config.storage.embeddings_prefix
        self.indexes_prefix = processing_config.storage.indexes_prefix
