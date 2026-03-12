"""Config extraction for worker_chunk_text startup."""

from collections.abc import Mapping
from typing import Any

from contracts.contracts import (
    ChunkTextJobConfigContract,
    ChunkTextProcessingConfigContract,
    RuntimeStoragePathsContract,
)
from pipeline_common.startup import WorkerConfigExtractor


class ChunkTextConfigExtractor(WorkerConfigExtractor[ChunkTextProcessingConfigContract]):
    """Parse and validate worker_chunk_text config from job properties."""

    def __init__(self, *, env: str | None) -> None:
        self._env = env

    def extract(self, job_properties: Mapping[str, Any]) -> ChunkTextProcessingConfigContract:
        """Extract typed chunk_text worker config."""
        job_payload = job_properties["job"]
        job_contract: ChunkTextJobConfigContract = ChunkTextJobConfigContract.from_dict(job_payload)
        return ChunkTextProcessingConfigContract(
            storage=RuntimeStoragePathsContract.from_raw(job_contract.storage, env=self._env),
            poll_interval_seconds=job_contract.poll_interval_seconds,
        )
