"""Config extraction for worker_chunk_text startup."""

from collections.abc import Mapping
from typing import Any

from configs.chunk_text_worker_config import (
    ChunkTextJobConfigContract,
    ChunkTextQueueConfigContract,
    ChunkTextWorkerConfig,
)
from pipeline_common.startup import WorkerConfigExtractor


class ChunkTextConfigExtractor(WorkerConfigExtractor[ChunkTextWorkerConfig]):
    """Parse and validate worker_chunk_text config from job properties."""

    def extract(self, job_properties: Mapping[str, Any]) -> ChunkTextWorkerConfig:
        """Extract typed chunk_text worker config."""
        job_config = job_properties["job"]
        storage = job_config["storage"]
        queue = job_config["queue"]
        job_contract = ChunkTextJobConfigContract(
            bucket=storage["bucket"],
            input_prefix=storage["input_prefix"],
            output_prefix=storage["output_prefix"],
            poll_interval_seconds=int(job_config["poll_interval_seconds"]),
        )
        queue_contract = ChunkTextQueueConfigContract(
            stage=queue["stage"],
            queue_pop_timeout_seconds=int(queue["queue_pop_timeout_seconds"]),
            pop_timeout_seconds=int(queue["pop_timeout_seconds"]),
            consume=queue["consume"],
            produce=queue["produce"],
            dlq=queue["dlq"],
        )
        return ChunkTextWorkerConfig(
            bucket=job_contract.bucket,
            input_prefix=job_contract.input_prefix,
            output_prefix=job_contract.output_prefix,
            poll_interval_seconds=job_contract.poll_interval_seconds,
            queue_config=queue_contract,
        )
