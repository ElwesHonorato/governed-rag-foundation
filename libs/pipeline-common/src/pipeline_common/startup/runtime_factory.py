"""Runtime context assembly for worker startup."""

from pipeline_common.gateways.lineage.contracts import DataHubDataJobKey
from pipeline_common.gateways.factories.lineage_gateway_factory import DataHubLineageGatewayBuilder
from pipeline_common.gateways.factories.object_storage_gateway_factory import ObjectStorageGatewayBuilder
from pipeline_common.gateways.factories.queue_gateway_factory import StageQueueGatewayBuilder
from pipeline_common.settings import SettingsBundle
from pipeline_common.startup.job_properties import JobPropertiesParser
from pipeline_common.startup.runtime_context import WorkerRuntimeContext


class RuntimeContextFactory:
    """Factory for shared runtime settings and initialized gateways."""

    def __init__(
        self,
        *,
        data_job_key: DataHubDataJobKey,
        settings_bundle: SettingsBundle,
    ) -> None:
        self._data_job_key = data_job_key
        self._settings_bundle = settings_bundle
        self.runtime_context = self._build_runtime_context()

    def _build_runtime_context(self) -> WorkerRuntimeContext:
        """Resolve shared runtime dependencies required by every worker."""
        lineage_gateway = DataHubLineageGatewayBuilder(
            datahub_settings=self._settings_bundle.datahub,
            data_job_key=self._data_job_key,
        ).build()
        job_properties = JobPropertiesParser(lineage_gateway.resolved_job_config.custom_properties).job_properties
        object_storage_gateway = ObjectStorageGatewayBuilder(
            s3_settings=self._settings_bundle.storage
        ).build()
        stage_queue_gateway = StageQueueGatewayBuilder(
            queue_settings=self._settings_bundle.queue,
            queue_config=job_properties["job"]["queue"],
        ).build()
        return WorkerRuntimeContext(
            lineage_gateway=lineage_gateway,
            object_storage_gateway=object_storage_gateway,
            stage_queue_gateway=stage_queue_gateway,
            job_properties=job_properties,
        )
