"""Config extraction for worker_scan startup."""

from collections.abc import Mapping
from typing import Any

from contracts.contracts import (
    ScanJobConfigContract,
    ScanQueueConfigContract,
    ScanStorageContract,
    ScanWorkerConfigContract,
)
from pipeline_common.startup import WorkerConfigExtractor


class ScanConfigExtractor(WorkerConfigExtractor[ScanWorkerConfigContract]):
    """Parse and validate worker_scan config from DataHub job properties."""

    def extract(self, job_properties: Mapping[str, Any]) -> ScanWorkerConfigContract:
        """Extract typed scan worker config."""
        job_config = job_properties["job"]
        storage = job_config["storage"]
        queue = job_config["queue"]
        job_contract = ScanJobConfigContract(
            bucket=storage["bucket"],
            source_prefix=storage["source_prefix"],
            output_prefix=storage["output_prefix"],
            poll_interval_seconds=int(job_config["poll_interval_seconds"]),
        )
        queue_contract = ScanQueueConfigContract(
            stage=queue["stage"],
            queue_pop_timeout_seconds=int(queue["queue_pop_timeout_seconds"]),
            pop_timeout_seconds=int(queue["pop_timeout_seconds"]),
            produce=queue["produce"],
            dlq=queue["dlq"],
            consume=queue.get("consume", ""),
        )
        return ScanWorkerConfigContract(
            storage=ScanStorageContract(
                bucket=job_contract.bucket,
                source_prefix=job_contract.source_prefix,
                output_prefix=job_contract.output_prefix,
            ),
            poll_interval_seconds=job_contract.poll_interval_seconds,
            queue_config=queue_contract,
        )
