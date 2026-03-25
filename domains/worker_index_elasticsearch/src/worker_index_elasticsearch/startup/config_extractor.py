"""Config extraction for worker_index_elasticsearch startup."""

from collections.abc import Mapping
from typing import Any

from pipeline_common.startup import WorkerConfigExtractor
from worker_index_elasticsearch.startup.contracts import (
    RawIndexElasticsearchJobConfig,
    RuntimeIndexElasticsearchJobConfig,
)


class IndexElasticsearchConfigExtractor(WorkerConfigExtractor[RuntimeIndexElasticsearchJobConfig]):
    """Parse and validate worker_index_elasticsearch config from job properties."""

    def extract(
        self,
        job_properties: Mapping[str, Any],
        *,
        env: str | None = None,
    ) -> RuntimeIndexElasticsearchJobConfig:
        """Extract typed startup config for the Elasticsearch indexing worker."""
        del env
        raw_job_config = RawIndexElasticsearchJobConfig.from_dict(job_properties["job"])
        return RuntimeIndexElasticsearchJobConfig.from_raw(raw_job_config)
