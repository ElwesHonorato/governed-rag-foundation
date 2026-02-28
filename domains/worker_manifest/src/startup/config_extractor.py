"""Config extraction for worker_manifest startup."""

from collections.abc import Mapping
from typing import Any

from configs.manifest_worker_config import ManifestJobConfigContract, ManifestStorageConfigContract, ManifestWorkerConfig
from pipeline_common.startup import WorkerConfigExtractor


class ManifestConfigExtractor(WorkerConfigExtractor[ManifestWorkerConfig]):
    """Parse and validate worker_manifest config from job properties."""

    def extract(self, job_properties: Mapping[str, Any]) -> ManifestWorkerConfig:
        """Extract typed manifest worker config."""
        job_config = job_properties["job"]
        storage = job_config["storage"]
        storage_contract = ManifestStorageConfigContract(
            bucket=storage["bucket"],
            processed_prefix=storage["processed_prefix"],
            chunks_prefix=storage["chunks_prefix"],
            embeddings_prefix=storage["embeddings_prefix"],
            indexes_prefix=storage["indexes_prefix"],
            manifest_prefix=storage["manifest_prefix"],
        )
        job_contract = ManifestJobConfigContract(
            poll_interval_seconds=int(job_config["poll_interval_seconds"]),
            storage=storage_contract,
        )
        return ManifestWorkerConfig(
            poll_interval_seconds=job_contract.poll_interval_seconds,
            storage=job_contract.storage,
        )
