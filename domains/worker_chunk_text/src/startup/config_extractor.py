"""Config extraction for worker_chunk_text startup."""

from collections.abc import Mapping
from typing import Any

from contracts.contracts import (
    ChunkTextJobConfigContract,
)
from pipeline_common.startup import WorkerConfigExtractor
from startup.storage_config_builder import EnvStorageConfigBuilder


class ChunkTextConfigExtractor(WorkerConfigExtractor[ChunkTextJobConfigContract]):
    """Parse and validate worker_chunk_text config from job properties."""

    def __init__(self, *, env: str | None) -> None:
        self._env = env

    def extract(self, job_properties: Mapping[str, Any]) -> ChunkTextJobConfigContract:
        """Extract typed chunk_text worker config."""
        job_payload = job_properties["job"]
        job_contract: ChunkTextJobConfigContract = ChunkTextJobConfigContract.from_dict(job_payload)
        return ChunkTextJobConfigContract(
            storage=EnvStorageConfigBuilder(
                env=self._env,
                storage_config=job_contract.storage,
            ).build(),
            poll_interval_seconds=job_contract.poll_interval_seconds,
        )
