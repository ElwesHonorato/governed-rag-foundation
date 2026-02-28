"""Config extraction for worker_scan startup."""

from collections.abc import Mapping
from typing import Any

from configs.scan_worker_config import ScanJobConfigContract, ScanQueueConfigContract, ScanWorkerConfig
from pipeline_common.startup import WorkerConfigExtractor


class ScanConfigExtractor(WorkerConfigExtractor[ScanWorkerConfig]):
    """Parse and validate worker_scan config from DataHub job properties."""

    def extract(self, job_properties: Mapping[str, Any]) -> ScanWorkerConfig:
        """Extract typed scan worker config."""
        job_config = job_properties["job"]
        storage = job_config["storage"]
        queue = job_config["queue"]
        job_contract = ScanJobConfigContract(
            bucket=storage["bucket"],
            input_prefix=storage["input_prefix"],
            output_prefix=storage["output_prefix"],
            poll_interval_seconds=job_config["poll_interval_seconds"],
        )
        queue_contract = ScanQueueConfigContract(
            stage=queue["stage"],
            queue_pop_timeout_seconds=queue["queue_pop_timeout_seconds"],
            pop_timeout_seconds=queue["pop_timeout_seconds"],
            produce=queue["produce"],
            dlq=queue["dlq"],
            consume=queue.get("consume", ""),
        )
        return ScanWorkerConfig(
            bucket=job_contract.bucket,
            input_prefix=job_contract.input_prefix,
            output_prefix=job_contract.output_prefix,
            poll_interval_seconds=job_contract.poll_interval_seconds,
            queue_config=queue_contract,
        )
