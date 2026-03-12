"""Config extraction for worker_parse_document startup."""

from collections.abc import Mapping
from typing import Any

from contracts.startup import (
    ParseSecurityConfigContract,
    RawParseJobConfig,
    RuntimeParseJobConfig,
)
from pipeline_common.startup import WorkerConfigExtractor


class ParseConfigExtractor(WorkerConfigExtractor[RuntimeParseJobConfig]):
    """Parse and validate worker_parse_document config from job properties."""

    def extract(self, job_properties: Mapping[str, Any]) -> RuntimeParseJobConfig:
        """Extract typed parse worker config."""
        raw_job_config_payload = job_properties["job"]
        raw_job_config: RawParseJobConfig = RawParseJobConfig.from_dict(raw_job_config_payload)
        return RuntimeParseJobConfig(
            storage=raw_job_config.storage,
            poll_interval_seconds=raw_job_config.poll_interval_seconds,
            security=ParseSecurityConfigContract(clearance=raw_job_config.security_clearance),
        )
