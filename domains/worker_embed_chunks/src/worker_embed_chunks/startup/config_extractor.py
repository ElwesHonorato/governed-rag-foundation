"""Config extraction for worker_embed_chunks startup."""

from collections.abc import Mapping
from typing import Any

from pipeline_common.startup import WorkerConfigExtractor
from worker_embed_chunks.startup.contracts import (
    RawEmbedChunksJobConfig,
    RuntimeEmbedChunksJobConfig,
    RuntimeEmbedChunksStorageConfig,
)


class EmbedChunksConfigExtractor(WorkerConfigExtractor[RuntimeEmbedChunksJobConfig]):
    """Parse and validate worker_embed_chunks config from job properties."""

    def extract(
        self,
        job_properties: Mapping[str, Any],
        *,
        env: str | None = None,
    ) -> RuntimeEmbedChunksJobConfig:
        """Extract typed embed_chunks worker config."""
        raw_job_config_payload = dict(job_properties["job"])
        raw_job_config: RawEmbedChunksJobConfig = RawEmbedChunksJobConfig.from_dict(raw_job_config_payload)
        return RuntimeEmbedChunksJobConfig(
            storage=RuntimeEmbedChunksStorageConfig.from_raw(raw_job_config.storage, env=env),
            poll_interval_seconds=raw_job_config.poll_interval_seconds,
            dimension=raw_job_config.dimension,
        )
