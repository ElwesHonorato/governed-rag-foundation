"""Config extraction for worker_embed_chunks startup."""

import os
from collections.abc import Mapping
from typing import Any

from configs.embed_chunks_worker_config import (
    EmbedChunksJobConfigContract,
    EmbedChunksQueueConfigContract,
    EmbedChunksWorkerConfig,
)
from pipeline_common.startup import WorkerConfigExtractor


class EmbedChunksConfigExtractor(WorkerConfigExtractor[EmbedChunksWorkerConfig]):
    """Parse and validate worker_embed_chunks config from job properties."""

    def extract(self, job_properties: Mapping[str, Any]) -> EmbedChunksWorkerConfig:
        """Extract typed embed_chunks worker config."""
        job_config = job_properties["job"]
        storage = job_config["storage"]
        queue = job_config["queue"]
        job_contract = EmbedChunksJobConfigContract(
            bucket=storage["bucket"],
            input_prefix=storage["input_prefix"],
            output_prefix=storage["output_prefix"],
            poll_interval_seconds=int(job_config["poll_interval_seconds"]),
            dimension=int(job_config.get("dimension", os.getenv("EMBEDDING_DIM", "32"))),
        )
        queue_contract = EmbedChunksQueueConfigContract(
            stage=queue["stage"],
            queue_pop_timeout_seconds=int(queue["queue_pop_timeout_seconds"]),
            pop_timeout_seconds=int(queue["pop_timeout_seconds"]),
            consume=queue["consume"],
            produce=queue["produce"],
            dlq=queue["dlq"],
        )
        return EmbedChunksWorkerConfig(
            bucket=job_contract.bucket,
            input_prefix=job_contract.input_prefix,
            output_prefix=job_contract.output_prefix,
            poll_interval_seconds=job_contract.poll_interval_seconds,
            dimension=job_contract.dimension,
            queue_config=queue_contract,
        )
