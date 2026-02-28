"""Shared worker startup helpers.

These utilities keep worker entrypoints orchestration-focused while
reusing common bootstrapping patterns across workers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, Mapping, TypeVar

from pipeline_common.lineage.contracts import DataHubDataJobKey
from pipeline_common.lineage.data_hub import DataHubRunTimeLineage
from pipeline_common.lineage.data_hub.contracts import DataHubLineageRuntimeConfig, DataHubRuntimeConnectionSettings
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.queue import StageQueue
from pipeline_common.settings import (
    DataHubSettings,
    QueueRuntimeSettings,
    S3StorageSettings,
)

TWorkerConfig = TypeVar("TWorkerConfig")
TWorkerService = TypeVar("TWorkerService", bound="WorkerService")


class WorkerService(ABC):
    """Long-running worker contract."""

    @abstractmethod
    def serve(self) -> None:
        """Start serving worker loop."""


class WorkerConfigExtractor(Generic[TWorkerConfig], ABC):
    """Extractor contract for typed worker config."""

    @abstractmethod
    def extract(self, job_properties: Mapping[str, Any]) -> TWorkerConfig:
        """Parse and validate resolved worker job properties."""


class WorkerServiceFactory(Generic[TWorkerConfig, TWorkerService], ABC):
    """Factory contract for worker service construction."""

    @abstractmethod
    def build(
        self,
        runtime: "WorkerRuntimeContext",
        worker_config: TWorkerConfig,
    ) -> TWorkerService:
        """Build worker service from runtime context + typed config."""


class WorkerRuntimeLauncher(Generic[TWorkerConfig, TWorkerService]):
    """Launch worker runtime from injected startup collaborators."""

    def __init__(
        self,
        *,
        data_job_key: DataHubDataJobKey,
        config_extractor: WorkerConfigExtractor[TWorkerConfig],
        service_factory: WorkerServiceFactory[TWorkerConfig, TWorkerService],
    ) -> None:
        self._data_job_key = data_job_key
        self._config_extractor = config_extractor
        self._service_factory = service_factory

    def start(self) -> None:
        """Execute the standard worker startup pipeline."""
        runtime_factory = RuntimeContextFactory(data_job_key=self._data_job_key)
        runtime = runtime_factory.runtime_context
        worker_config = self._config_extractor.extract(runtime.job_properties)
        service = self._service_factory.build(runtime, worker_config)
        service.serve()


@dataclass(frozen=True)
class WorkerRuntimeContext:
    """Runtime dependencies resolved by startup bootstrap."""

    lineage_gateway: DataHubRunTimeLineage
    object_storage_gateway: ObjectStorageGateway
    stage_queue_gateway: StageQueue
    job_properties: dict[str, Any]


class RuntimeContextFactory:
    """Factory for shared runtime settings and initialized gateways."""

    def __init__(self, *, data_job_key: DataHubDataJobKey) -> None:
        self._data_job_key = data_job_key
        self.runtime_context = self._build_runtime_context()

    def _build_runtime_context(self) -> WorkerRuntimeContext:
        """Resolve shared runtime dependencies required by every worker."""
        lineage_gateway = self._build_lineage_gateway()
        job_properties = self._derive_job_properties(lineage_gateway)
        object_storage_gateway = self._build_object_storage_gateway()
        stage_queue_gateway = self._build_stage_queue_gateway(job_properties)
        return WorkerRuntimeContext(
            lineage_gateway=lineage_gateway,
            object_storage_gateway=object_storage_gateway,
            stage_queue_gateway=stage_queue_gateway,
            job_properties=job_properties,
        )

    def _derive_job_properties(self, lineage_gateway: DataHubRunTimeLineage) -> dict[str, Any]:
        """Derive nested job properties from resolved DataHub custom properties."""
        return JobPropertiesParser(lineage_gateway.resolved_job_config.custom_properties).job_properties

    def _build_lineage_gateway(self) -> DataHubRunTimeLineage:
        """Build DataHub runtime lineage gateway."""
        return DataHubLineageGatewayBuilder(
            datahub_settings=DataHubSettings.from_env(),
            data_job_key=self._data_job_key,
        ).build()

    def _build_object_storage_gateway(self) -> ObjectStorageGateway:
        """Build object storage gateway."""
        return ObjectStorageGatewayBuilder(
            s3_settings=S3StorageSettings.from_env()
        ).build()

    def _build_stage_queue_gateway(self, job_properties: dict[str, Any]) -> StageQueue:
        """Build stage queue gateway."""
        return StageQueueGatewayBuilder(
            queue_settings=QueueRuntimeSettings.from_env(),
            queue_config=job_properties["job"]["queue"],
        ).build()

class JobPropertiesParser:
    """Parser for worker DataHub job custom properties."""

    def __init__(self, custom_properties: Mapping[str, str]) -> None:
        self.custom_properties = custom_properties
        self.job_properties = self._build_properties()

    def _set_nested(self, target: dict[str, Any], dotted_key: str, value: str) -> None:
        """Set one dotted key (for example, 'job.storage.bucket') into nested dict."""

        def _insert(node: dict[str, Any], parts: list[str], final_value: str) -> None:
            head = parts[0]
            if len(parts) == 1:
                node[head] = final_value
                return
            child = node.setdefault(head, {})
            _insert(child, parts[1:], final_value)

        _insert(target, dotted_key.split("."), value)

    def _build_properties(self) -> dict[str, Any]:
        """Build nested mapping from dot-notation custom properties."""
        expanded: dict[str, Any] = {}
        for key, value in self.custom_properties.items():
            if "." in key:
                self._set_nested(expanded, key, value)
        return expanded


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


class ObjectStorageGatewayBuilder:
    """Build object storage gateway from S3 runtime settings."""

    def __init__(self, *, s3_settings: S3StorageSettings) -> None:
        self.s3_settings = s3_settings

    def build(self) -> ObjectStorageGateway:
        """Build object storage gateway for one worker."""
        return ObjectStorageGateway(
            S3Client(
                endpoint_url=self.s3_settings.s3_endpoint,
                access_key=self.s3_settings.s3_access_key,
                secret_key=self.s3_settings.s3_secret_key,
                region_name=self.s3_settings.aws_region,
            )
        )


class StageQueueGatewayBuilder:
    """Build stage queue gateway from queue runtime settings and job config."""

    def __init__(self, *, queue_settings: QueueRuntimeSettings, queue_config: dict[str, Any]) -> None:
        self.queue_settings = queue_settings
        self.queue_config = queue_config

    def build(self) -> StageQueue:
        """Build stage queue gateway for one worker."""
        return StageQueue(
            self.queue_settings.broker_url,
            queue_config=self.queue_config,
        )
