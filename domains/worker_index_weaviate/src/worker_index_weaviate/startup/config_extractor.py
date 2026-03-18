"""Config extraction for worker_index_weaviate startup."""
from collections.abc import Mapping
from typing import Any

from pipeline_common.helpers.config import _required_env
from pipeline_common.startup import WorkerConfigExtractor
from worker_index_weaviate.startup.contracts import (
    RawIndexWeaviateJobConfig,
    RuntimeIndexWeaviateJobConfig,
    RuntimeIndexWeaviateStorageConfig,
)


class IndexWeaviateConfigExtractor(WorkerConfigExtractor[RuntimeIndexWeaviateJobConfig]):
    """Parse and validate worker_index_weaviate config from job properties."""

    def extract(
        self,
        job_properties: Mapping[str, Any],
        *,
        env: str | None = None,
    ) -> RuntimeIndexWeaviateJobConfig:
        """Extract typed index_weaviate worker config."""
        raw_job_config_payload = job_properties["job"]
        raw_job_config: RawIndexWeaviateJobConfig = RawIndexWeaviateJobConfig.from_dict(raw_job_config_payload)
        return RuntimeIndexWeaviateJobConfig(
            storage=RuntimeIndexWeaviateStorageConfig.from_raw(raw_job_config.storage, env=env),
            poll_interval_seconds=raw_job_config.poll_interval_seconds,
            weaviate_url=_required_env("WEAVIATE_URL"),
        )
