from pipeline_common.lineage.data_hub.constants import DataHubStageFlowConfig
from pipeline_common.settings import DataHubBootstrapSettings

from .lineage import DataHubLineageClient


class DataHubDataFlowBuilder:
    """Build and upsert DataFlow/DataJob templates from stage enum config."""

    def __init__(
        self,
        stage_enum: type[DataHubStageFlowConfig],
        settings: DataHubBootstrapSettings,
    ) -> None:
        self.stages = list(stage_enum)
        self.settings = settings

    def upsert_stage(self, client: DataHubLineageClient, stage: DataHubStageFlowConfig) -> None:
        """Upsert one stage's flow and job template."""
        stage_config = stage.value
        client.upsert_flow_and_job(
            flow_platform=stage_config.flow_platform,
            flow_name=stage_config.flow_name,
            flow_instance=client.env,
            job_name=stage_config.job_name,
        )

    def upsert_all(self) -> None:
        """Upsert all configured stage templates in order."""
        bootstrap_client = DataHubLineageClient(
            stage=self.stages[0],
            settings=self.settings,
        )
        for stage in self.stages:
            self.upsert_stage(bootstrap_client, stage)
