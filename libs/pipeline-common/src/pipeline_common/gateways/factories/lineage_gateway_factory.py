"""DataHub lineage gateway factory for worker runtime."""

from pipeline_common.gateways.lineage.contracts import DataHubDataJobKey
from pipeline_common.gateways.lineage import DataHubRuntimeLineage
from pipeline_common.gateways.lineage.runtime_contracts import (
    DataHubLineageRuntimeConfig,
    DataHubRuntimeConnectionSettings,
    LineageRuntimeGateway,
)
from pipeline_common.gateways.lineage.settings import DataHubSettings


class DataHubLineageGatewayFactory:
    """Create DataHub runtime lineage gateway from DataHub settings + job key."""

    def __init__(
        self,
        *,
        datahub_settings: DataHubSettings,
        data_job_key: DataHubDataJobKey,
        env: str | None = None,
    ) -> None:
        self.datahub_settings = datahub_settings
        self.data_job_key = data_job_key
        self.env = env

    def build(self) -> LineageRuntimeGateway:
        """Create and initialize runtime lineage gateway for one worker."""
        gateway = DataHubRuntimeLineage(
            client_config=DataHubLineageRuntimeConfig(
                connection_settings=DataHubRuntimeConnectionSettings(
                    server=self.datahub_settings.server,
                    env=self.env,
                    token=self.datahub_settings.token,
                    timeout_sec=self.datahub_settings.timeout_sec,
                    retry_max_times=self.datahub_settings.retry_max_times,
                ),
                data_job_key=self.data_job_key,
            )
        )
        gateway.resolve_job_metadata()
        return gateway
