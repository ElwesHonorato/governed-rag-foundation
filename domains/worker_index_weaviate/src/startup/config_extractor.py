"""Config extraction for worker_index_weaviate startup."""

from collections.abc import Mapping
from typing import Any

from contracts.index_weaviate_worker_contracts import (
    IndexWeaviateJobConfigContract,
    IndexWeaviateQueueConfigContract,
    IndexWeaviateStorageConfigContract,
    IndexWeaviateWorkerConfigContract,
)
from pipeline_common.startup import WorkerConfigExtractor


class IndexWeaviateConfigExtractor(WorkerConfigExtractor[IndexWeaviateWorkerConfigContract]):
    """Parse and validate worker_index_weaviate config from job properties."""

    def extract(self, job_properties: Mapping[str, Any]) -> IndexWeaviateWorkerConfigContract:
        """Extract typed index_weaviate worker config."""
        job_config = job_properties["job"]
        storage = job_config["storage"]
        queue = job_config["queue"]
        job_contract = IndexWeaviateJobConfigContract(
            bucket=storage["bucket"],
            input_prefix=storage["input_prefix"],
            output_prefix=storage["output_prefix"],
            poll_interval_seconds=int(job_config["poll_interval_seconds"]),
        )
        queue_contract = IndexWeaviateQueueConfigContract(
            stage=queue["stage"],
            queue_pop_timeout_seconds=int(queue["queue_pop_timeout_seconds"]),
            pop_timeout_seconds=int(queue["pop_timeout_seconds"]),
            consume=queue["consume"],
            dlq=queue["dlq"],
        )
        return IndexWeaviateWorkerConfigContract(
            storage=IndexWeaviateStorageConfigContract(
                bucket=job_contract.bucket,
                input_prefix=job_contract.input_prefix,
                output_prefix=job_contract.output_prefix,
            ),
            poll_interval_seconds=job_contract.poll_interval_seconds,
            queue_config=queue_contract,
        )
