"""Config extraction for worker_chunk_text startup."""

from collections.abc import Mapping
from typing import Any

from contracts.startup import (
    RawChunkJobConfigContract,
    RuntimeChunkJobConfigContract,
    RuntimeStoragePathsContract,
)
from pipeline_common.startup import WorkerConfigExtractor


class ChunkTextConfigExtractor(WorkerConfigExtractor[RuntimeChunkJobConfigContract]):
    """Parse and validate worker_chunk_text config from job properties."""

    def extract(
        self,
        job_properties: Mapping[str, Any],
        *,
        env: str | None = None,
    ) -> RuntimeChunkJobConfigContract:
        """Extract typed chunk_text worker config."""
        job_payload = job_properties["job"]
        job_contract: RawChunkJobConfigContract = RawChunkJobConfigContract.from_dict(job_payload)
        return RuntimeChunkJobConfigContract(
            storage=RuntimeStoragePathsContract.from_raw(job_contract.storage, env=env),
            poll_interval_seconds=job_contract.poll_interval_seconds,
        )
