"""Config extraction for worker_scan startup."""

from collections.abc import Mapping
from typing import Any

from pipeline_common.startup import WorkerConfigExtractor
from startup.contracts import RawScanJobConfig, RuntimeScanJobConfig, RuntimeScanStorageConfig


class ScanConfigExtractor(WorkerConfigExtractor[RuntimeScanJobConfig]):
    """Parse and validate worker_scan config from DataHub job properties."""

    def extract(self, job_properties: Mapping[str, Any]) -> RuntimeScanJobConfig:
        """Extract typed scan worker config."""
        raw_job_config_payload = job_properties["job"]
        raw_job_config: RawScanJobConfig = RawScanJobConfig.from_dict(raw_job_config_payload)
        return RuntimeScanJobConfig(
            storage=RuntimeScanStorageConfig.from_raw(raw_job_config.storage),
            poll_interval_seconds=raw_job_config.poll_interval_seconds,
        )
