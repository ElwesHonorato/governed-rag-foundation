"""Config extraction for worker_chunk_text startup."""

from collections.abc import Mapping
from typing import Any

from contracts.contracts import (
    ChunkTextJobConfigContract,
    ChunkTextWorkerConfigContract,
)
from pipeline_common.startup import WorkerConfigExtractor


class ChunkTextConfigExtractor(WorkerConfigExtractor[ChunkTextWorkerConfigContract]):
    """Parse and validate worker_chunk_text config from job properties."""

    def extract(self, job_properties: Mapping[str, Any]) -> ChunkTextWorkerConfigContract:
        """Extract typed chunk_text worker config."""
        job_payload = job_properties["job"]
        job_contract = ChunkTextJobConfigContract.from_dict(job_payload)
        return ChunkTextWorkerConfigContract.from_dict(
            {
                "storage": job_payload["storage"],
                "poll_interval_seconds": job_contract.poll_interval_seconds,
                "queue_config": job_payload["queue"],
            }
        )
