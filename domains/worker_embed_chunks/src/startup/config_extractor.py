"""Config extraction for worker_embed_chunks startup."""

import os
from collections.abc import Mapping
from typing import Any

from contracts.contracts import (
    EmbedChunksJobConfigContract,
    EmbedChunksQueueConfigContract,
    EmbedChunksStorageConfigContract,
    EmbedChunksWorkerConfigContract,
)
from pipeline_common.startup import WorkerConfigExtractor


class EmbedChunksConfigExtractor(WorkerConfigExtractor[EmbedChunksWorkerConfigContract]):
    """Parse and validate worker_embed_chunks config from job properties."""

    def extract(self, job_properties: Mapping[str, Any]) -> EmbedChunksWorkerConfigContract:
        """Extract typed embed_chunks worker config."""
        job_config = job_properties["job"]
        storage = job_config["storage"]
        queue = job_config["queue"]
        job_contract = EmbedChunksJobConfigContract(
            bucket=storage["bucket"],
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
        return EmbedChunksWorkerConfigContract(
            storage=EmbedChunksStorageConfigContract(
                bucket=job_contract.bucket,
                output_prefix=job_contract.output_prefix,
            ),
            poll_interval_seconds=job_contract.poll_interval_seconds,
            dimension=job_contract.dimension,
            queue_config=queue_contract,
        )
