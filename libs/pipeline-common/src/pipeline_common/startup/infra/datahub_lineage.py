"""DataHub lineage gateway builder for worker runtime."""

from pipeline_common.lineage.contracts import DataHubDataJobKey
from pipeline_common.lineage import DataHubRunTimeLineage
from pipeline_common.lineage.runtime_contracts import DataHubLineageRuntimeConfig, DataHubRuntimeConnectionSettings
from pipeline_common.settings import DataHubSettings


class DataHubLineageGatewayBuilder:
    """Build DataHub runtime lineage gateway from DataHub settings + job key."""

    def __init__(self, *, datahub_settings: DataHubSettings, data_job_key: DataHubDataJobKey) -> None:
        self.datahub_settings = datahub_settings
        self.data_job_key = data_job_key

    def build(self) -> DataHubRunTimeLineage:
        """Build DataHub runtime lineage gateway for one worker."""
        return DataHubRunTimeLineage(
            client_config=DataHubLineageRuntimeConfig(
                connection_settings=DataHubRuntimeConnectionSettings(
                    server=self.datahub_settings.server,
                    env=self.datahub_settings.env,
                    token=self.datahub_settings.token,
                    timeout_sec=self.datahub_settings.timeout_sec,
                    retry_max_times=self.datahub_settings.retry_max_times,
                ),
                data_job_key=self.data_job_key,
            )
        )
