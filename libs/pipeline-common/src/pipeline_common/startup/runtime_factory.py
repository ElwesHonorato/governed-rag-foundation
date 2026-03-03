"""Worker runtime context assembly.

Layer:
- Startup wiring/composition helper shared across worker domains.

Role:
- Build the shared runtime dependency bundle used by worker service factories.

Design intent:
- Centralize gateway construction and resolved job-properties extraction so
  worker domains keep composition roots small and consistent.

Non-goals:
- Does not execute worker business logic.
- Does not validate worker-specific configuration semantics.
"""

from pipeline_common.gateways.lineage.contracts import DataHubDataJobKey
from pipeline_common.gateways.factories.lineage_gateway_factory import DataHubLineageGatewayFactory
from pipeline_common.gateways.factories.object_storage_gateway_factory import ObjectStorageGatewayFactory
from pipeline_common.gateways.factories.queue_gateway_factory import StageQueueGatewayFactory
from pipeline_common.gateways.processing_engine import build_spark_session
from pipeline_common.settings import SettingsBundle
from pipeline_common.startup.job_properties import JobPropertiesParser
from pipeline_common.startup.runtime_context import WorkerRuntimeContext


class RuntimeContextFactory:
    """Build a ``WorkerRuntimeContext`` from settings and a DataHub job key.

    Layer:
    - Startup wiring/composition.

    Dependencies:
    - Gateway factories (lineage/object storage/queue).
    - Settings bundle loaded by ``SettingsProvider``.

    Design intent:
    - Create one place where shared runtime dependencies are assembled.

    Non-goals:
    - Not a long-lived service; this is startup-time construction logic.
    """

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
        lineage_gateway = DataHubLineageGatewayFactory(
            datahub_settings=self._settings_bundle.datahub,
            data_job_key=self._data_job_key,
        ).build()
        job_properties = JobPropertiesParser(lineage_gateway.resolved_job_config.custom_properties).job_properties
        object_storage_gateway = ObjectStorageGatewayFactory(
            s3_settings=self._settings_bundle.storage
        ).build()
        stage_queue_gateway = StageQueueGatewayFactory(
            queue_settings=self._settings_bundle.queue,
            queue_config=job_properties["job"]["queue"],
        ).build()
        spark_settings = self._settings_bundle.spark
        spark_session = None
        if spark_settings is not None:
            spark_session = build_spark_session(
                enabled=spark_settings.enabled,
                app_name=spark_settings.app_name,
                master_url=spark_settings.master_url,
            )
        return WorkerRuntimeContext(
            lineage_gateway=lineage_gateway,
            object_storage_gateway=object_storage_gateway,
            stage_queue_gateway=stage_queue_gateway,
            spark_session=spark_session,
            job_properties=job_properties,
        )
