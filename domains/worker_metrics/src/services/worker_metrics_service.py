import logging
import time

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
        poll_interval_seconds: int,
        storage_bucket: str,
        processed_prefix: str,
        chunks_prefix: str,
        embeddings_prefix: str,
        indexes_prefix: str,
        processor: MetricsCycleProcessor,
    ) -> None:
        """Initialize instance state and dependencies."""
        self._counters = counters
        self._storage_gateway = object_storage
        self._lineage_gateway = lineage
        self._poll_interval_seconds = poll_interval_seconds
        self._storage_bucket = storage_bucket
        self._processed_prefix = processed_prefix
        self._chunks_prefix = chunks_prefix
        self._embeddings_prefix = embeddings_prefix
        self._indexes_prefix = indexes_prefix
        self._processor = processor

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
        self._register_lineage_inputs()
        processed_keys = self._storage_gateway.list_keys(self._storage_bucket, self._processed_prefix)
        chunk_keys = self._storage_gateway.list_keys(self._storage_bucket, self._chunks_prefix)
        embedding_keys = self._storage_gateway.list_keys(self._storage_bucket, self._embeddings_prefix)
        indexed_keys = self._storage_gateway.list_keys(self._storage_bucket, self._indexes_prefix)
        counts = self._processor.build_counts(
            processed_keys=processed_keys,
            chunk_keys=chunk_keys,
            embedding_keys=embedding_keys,
            indexed_keys=indexed_keys,
        )

        self._counters.files_processed = counts["files_processed"]
        self._counters.chunks_created = counts["chunks_created"]
        self._counters.embedding_artifacts = counts["embedding_artifacts"]
        self._counters.index_upserts = counts["index_upserts"]
        self._counters.emit()
        self._lineage_gateway.complete_run()

    def _register_lineage_inputs(self) -> None:
        self._lineage_gateway.start_run()
        self._lineage_gateway.add_input(name=f"{self._storage_bucket}/{self._processed_prefix}", platform=DatasetPlatform.S3)
        self._lineage_gateway.add_input(name=f"{self._storage_bucket}/{self._chunks_prefix}", platform=DatasetPlatform.S3)
        self._lineage_gateway.add_input(name=f"{self._storage_bucket}/{self._embeddings_prefix}", platform=DatasetPlatform.S3)
        self._lineage_gateway.add_input(name=f"{self._storage_bucket}/{self._indexes_prefix}", platform=DatasetPlatform.S3)

    def _handle_metrics_cycle_failure(self, exc: Exception) -> None:
        self._lineage_gateway.fail_run(error_message=str(exc))
        logger.exception("Failed collecting pipeline metrics")

    def _sleep_until_next_cycle(self) -> None:
        time.sleep(self._poll_interval_seconds)
