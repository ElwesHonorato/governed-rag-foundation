"""Config extraction for worker_parse_document startup."""

from collections.abc import Mapping
from typing import Any

from contracts.contracts import (
    ParseJobConfigContract,
    ParseQueueConfigContract,
    ParseStorageConfigContract,
    ParseWorkerConfigContract,
)
from pipeline_common.startup import WorkerConfigExtractor


class ParseConfigExtractor(WorkerConfigExtractor[ParseWorkerConfigContract]):
    """Parse and validate worker_parse_document config from job properties."""

    def extract(self, job_properties: Mapping[str, Any]) -> ParseWorkerConfigContract:
        """Extract typed parse worker config."""
        job_config = job_properties["job"]
        storage = job_config["storage"]
        queue = job_config["queue"]
        security = job_config["security"]
        job_contract: ParseJobConfigContract = ParseJobConfigContract(
            bucket=storage["bucket"],
            output_prefix=storage["output_prefix"],
            poll_interval_seconds=int(job_config["poll_interval_seconds"]),
            security_clearance=security["clearance"],
        )
        queue_contract: ParseQueueConfigContract = ParseQueueConfigContract(
            stage=queue["stage"],
            queue_pop_timeout_seconds=int(queue["queue_pop_timeout_seconds"]),
            pop_timeout_seconds=int(queue["pop_timeout_seconds"]),
            consume=queue["consume"],
            produce=queue["produce"],
            dlq=queue["dlq"],
        )
        return ParseWorkerConfigContract(
            storage=ParseStorageConfigContract(
                bucket=job_contract.bucket,
                output_prefix=job_contract.output_prefix,
            ),
            poll_interval_seconds=job_contract.poll_interval_seconds,
            security_clearance=job_contract.security_clearance,
            queue_config=queue_contract,
        )
