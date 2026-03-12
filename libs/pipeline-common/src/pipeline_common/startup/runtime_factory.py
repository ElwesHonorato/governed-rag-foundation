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

from typing import Any, Mapping

from pipeline_common.gateways.lineage.contracts import DataHubDataJobKey
from pipeline_common.gateways.factories.lineage_gateway_factory import DataHubLineageGatewayFactory
from pipeline_common.gateways.factories.object_storage_gateway_factory import ObjectStorageGatewayFactory
from pipeline_common.gateways.factories.queue_gateway_factory import QueueGatewayFactory
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import QueueGateway
from pipeline_common.gateways.lineage.settings import DataHubSettings
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

    def build(self) -> WorkerRuntimeContext:
        """Resolve shared runtime dependencies required by every worker."""
        lineage_gateway = self._build_lineage_gateway()
        job_properties = JobPropertiesParser(lineage_gateway.resolved_job_config.custom_properties).job_properties
        object_storage_gateway = self._build_object_storage_gateway()
        stage_queue_gateway = self._build_stage_queue_gateway(job_properties=job_properties)
        return WorkerRuntimeContext(
            env=self._settings_bundle.env,
            lineage_gateway=lineage_gateway,
            object_storage_gateway=object_storage_gateway,
            stage_queue_gateway=stage_queue_gateway,
            job_properties=job_properties,
        )

    def _build_lineage_gateway(self) -> LineageRuntimeGateway:
        """Create lineage gateway from configured runtime settings."""
        datahub_settings = self._require_datahub_settings()
        return DataHubLineageGatewayFactory(
            datahub_settings=datahub_settings,
            data_job_key=self._data_job_key,
            env=self._settings_bundle.env,
        ).build()

    def _build_object_storage_gateway(self) -> ObjectStorageGateway | None:
        """Create object storage gateway from configured runtime settings."""
        storage_settings = self._settings_bundle.storage
        if storage_settings is None:
            return None
        return ObjectStorageGatewayFactory(
            s3_settings=storage_settings
        ).build()

    def _build_stage_queue_gateway(self, *, job_properties: Mapping[str, Any]) -> QueueGateway | None:
        """Create queue gateway from runtime settings and parsed job queue config."""
        queue_settings = self._settings_bundle.queue
        if queue_settings is None:
            return None
        queue_config = job_properties.get("job", {}).get("queue")
        if queue_config is None:
            return None
        if not isinstance(queue_config, dict):
            raise ValueError("job.queue must be a dictionary.")
        return QueueGatewayFactory(
            queue_settings=queue_settings,
            queue_config=queue_config,
        ).build()

    def _require_datahub_settings(self) -> DataHubSettings:
        datahub_settings = self._settings_bundle.datahub
        if datahub_settings is None:
            raise ValueError("RuntimeContextFactory requires datahub settings.")
        return datahub_settings
