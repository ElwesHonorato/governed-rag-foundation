"""Config extraction for worker_chunk_text startup."""

from collections.abc import Mapping
from typing import Any

from worker_chunk_text.startup.contracts import (
    RawChunkJobConfig,
    RuntimeChunkJobConfig,
    RuntimeChunkStorageConfig,
)
from pipeline_common.startup import WorkerConfigExtractor


class ChunkTextConfigExtractor(WorkerConfigExtractor[RuntimeChunkJobConfig]):
    """Parse and validate worker_chunk_text config from job properties."""

    def extract(
        self,
        job_properties: Mapping[str, Any],
        *,
        env: str | None = None,
    ) -> RuntimeChunkJobConfig:
        """Extract typed startup configuration for the chunk-text worker.

        Args:
            job_properties: Resolved job properties containing the ``job`` payload.
            env: Optional environment name used to scope runtime storage prefixes.

        Returns:
            Parsed runtime configuration for service assembly.
        """
        raw_job_config_payload = job_properties["job"]
        raw_job_config: RawChunkJobConfig = RawChunkJobConfig.from_dict(raw_job_config_payload)
        return RuntimeChunkJobConfig(
            storage=RuntimeChunkStorageConfig.from_raw(raw_job_config.storage, env=env),
            poll_interval_seconds=raw_job_config.poll_interval_seconds,
        )
