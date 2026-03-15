"""Config extraction for worker_parse_document startup."""

from collections.abc import Mapping
from typing import Any

from worker_parse_document.startup.contracts import (
    RawParseJobConfig,
    RuntimeParseJobConfig,
    RuntimeParseSecurityConfig,
    RuntimeParseStorageConfig,
)
from pipeline_common.startup import WorkerConfigExtractor


class ParseConfigExtractor(WorkerConfigExtractor[RuntimeParseJobConfig]):
    """Parse and validate worker_parse_document config from job properties."""

    def extract(
        self,
        job_properties: Mapping[str, Any],
        *,
        env: str | None = None,
    ) -> RuntimeParseJobConfig:
        """Extract typed parse worker config."""
        raw_job_config_payload = job_properties["job"]
        raw_job_config: RawParseJobConfig = RawParseJobConfig.from_dict(raw_job_config_payload)
        return RuntimeParseJobConfig(
            storage=RuntimeParseStorageConfig.from_raw(raw_job_config.storage, env=env),
            poll_interval_seconds=raw_job_config.poll_interval_seconds,
            security=RuntimeParseSecurityConfig(clearance=raw_job_config.security_clearance),
        )
