"""Config extraction for worker_embed_chunks startup."""

import os
from collections.abc import Mapping
from typing import Any

from contracts.startup import RawEmbedChunksJobConfig, RuntimeEmbedChunksJobConfig
from pipeline_common.startup import WorkerConfigExtractor


class EmbedChunksConfigExtractor(WorkerConfigExtractor[RuntimeEmbedChunksJobConfig]):
    """Parse and validate worker_embed_chunks config from job properties."""

    def extract(self, job_properties: Mapping[str, Any]) -> RuntimeEmbedChunksJobConfig:
        """Extract typed embed_chunks worker config."""
        raw_job_config_payload = dict(job_properties["job"])
        raw_job_config_payload.setdefault("dimension", os.getenv("EMBEDDING_DIM", "32"))
        raw_job_config: RawEmbedChunksJobConfig = RawEmbedChunksJobConfig.from_dict(raw_job_config_payload)
        return RuntimeEmbedChunksJobConfig(
            storage=raw_job_config.storage,
            poll_interval_seconds=raw_job_config.poll_interval_seconds,
            dimension=raw_job_config.dimension,
        )
