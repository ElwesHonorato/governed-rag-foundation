"""Runtime context assembly for worker startup."""

from typing import Any

from pipeline_common.lineage.contracts import DataHubDataJobKey
from pipeline_common.settings import DataHubSettings, QueueRuntimeSettings, S3StorageSettings
from pipeline_common.startup.infra.datahub_lineage import DataHubLineageGatewayBuilder
from pipeline_common.startup.infra.object_storage import ObjectStorageGatewayBuilder
from pipeline_common.startup.infra.stage_queue import StageQueueGatewayBuilder
from pipeline_common.startup.job_properties import derive_job_properties
from pipeline_common.startup.runtime_context import WorkerRuntimeContext


class RuntimeContextFactory:
    """Factory for shared runtime settings and initialized gateways."""

    def __init__(self, *, data_job_key: DataHubDataJobKey) -> None:
        self._data_job_key = data_job_key
        self.runtime_context = self._build_runtime_context()

    def _build_runtime_context(self) -> WorkerRuntimeContext:
        """Resolve shared runtime dependencies required by every worker."""
        lineage_gateway = DataHubLineageGatewayBuilder(
            datahub_settings=DataHubSettings.from_env(),
            data_job_key=self._data_job_key,
        ).build()
        job_properties = derive_job_properties(lineage_gateway.resolved_job_config.custom_properties)
        object_storage_gateway = ObjectStorageGatewayBuilder(
            s3_settings=S3StorageSettings.from_env()
        ).build()
        stage_queue_gateway = StageQueueGatewayBuilder(
            queue_settings=QueueRuntimeSettings.from_env(),
            queue_config=job_properties["job"]["queue"],
        ).build()
        return WorkerRuntimeContext(
            lineage_gateway=lineage_gateway,
            object_storage_gateway=object_storage_gateway,
            stage_queue_gateway=stage_queue_gateway,
            job_properties=job_properties,
        )
