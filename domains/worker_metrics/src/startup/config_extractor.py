"""Config extraction for worker_metrics startup."""

from collections.abc import Mapping
from typing import Any

from contracts.contracts import MetricsJobConfigContract, MetricsStorageConfigContract, MetricsWorkerConfigContract
from pipeline_common.startup import WorkerConfigExtractor


class MetricsConfigExtractor(WorkerConfigExtractor[MetricsWorkerConfigContract]):
    """Parse and validate worker_metrics config from job properties."""

    def extract(self, job_properties: Mapping[str, Any]) -> MetricsWorkerConfigContract:
        """Extract typed metrics worker config."""
        job_config = job_properties["job"]
        storage = job_config["storage"]
        storage_contract = MetricsStorageConfigContract(
            bucket=storage["bucket"],
            processed_prefix=storage["processed_prefix"],
            chunks_prefix=storage["chunks_prefix"],
            embeddings_prefix=storage["embeddings_prefix"],
            indexes_prefix=storage["indexes_prefix"],
        )
        job_contract = MetricsJobConfigContract(
            poll_interval_seconds=int(job_config["poll_interval_seconds"]),
            storage=storage_contract,
        )
        return MetricsWorkerConfigContract(
            poll_interval_seconds=job_contract.poll_interval_seconds,
            storage=job_contract.storage,
        )
