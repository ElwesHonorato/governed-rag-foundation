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
    def extract(self, custom_properties: Mapping[str, str]) -> TWorkerConfig:
        """Parse and validate raw DataHub custom properties."""


class WorkerServiceFactory(Generic[TWorkerConfig, TWorkerService], ABC):
    """Factory contract for worker service construction."""

    @abstractmethod
    def build(
        self,
        runtime: "WorkerRuntimeContext",
        infrastructure: "InfrastructureFactory",
        worker_config: TWorkerConfig,
    ) -> TWorkerService:
        """Build worker service from runtime context + typed config."""


class WorkerBootstrap(Generic[TWorkerConfig, TWorkerService], ABC):
    """Template method bootstrap for worker startup orchestration."""

    def __init__(
        self,
        *,
        runtime_factory: "RuntimeContextFactory",
    ) -> None:
        self.runtime_factory = runtime_factory

    def run(self) -> None:
        """Execute the standard worker startup pipeline."""
        runtime = self.runtime_factory.runtime_context
        infrastructure = InfrastructureFactory(runtime)
        lineage = infrastructure.datahub_lineage_client
        worker_config = self.config_extractor().extract(lineage.resolved_job_config.custom_properties)
        service = self.service_factory().build(runtime, infrastructure, worker_config)
        service.serve()

    @abstractmethod
    def data_job_key(self) -> DataHubDataJobKey:
        """Return DataHub job key for this worker."""

    @abstractmethod
    def config_extractor(self) -> WorkerConfigExtractor[TWorkerConfig]:
        """Return typed config extractor for this worker."""

    @abstractmethod
    def service_factory(self) -> WorkerServiceFactory[TWorkerConfig, TWorkerService]:
        """Return worker service factory."""


@dataclass(frozen=True)
class WorkerRuntimeContext:
    """Runtime dependencies resolved by startup bootstrap."""

    data_job_key: DataHubDataJobKey
    s3_settings: S3StorageSettings
    queue_settings: QueueRuntimeSettings
    datahub_settings: DataHubSettings


class RuntimeContextFactory:
    """Factory for shared runtime settings."""

    def __init__(self, *, data_job_key: DataHubDataJobKey) -> None:
        self._data_job_key = data_job_key
        self._s3_settings = S3StorageSettings.from_env()
        self._queue_settings = QueueRuntimeSettings.from_env()
        self._datahub_settings = DataHubSettings.from_env()
        self._runtime_context = self._build_runtime_context()

    def _build_runtime_context(self) -> WorkerRuntimeContext:
        """Resolve shared runtime dependencies required by every worker."""
        return WorkerRuntimeContext(
            data_job_key=self._data_job_key,
            s3_settings=self._s3_settings,
            queue_settings=self._queue_settings,
            datahub_settings=self._datahub_settings,
        )

    @property
    def runtime_context(self) -> WorkerRuntimeContext:
        """Expose initialized runtime context."""
        return self._runtime_context


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


class InfrastructureFactory:
    """Factory for queue and object storage infrastructure clients."""

    def __init__(self, runtime_context: WorkerRuntimeContext) -> None:
        self.runtime_context = runtime_context
        self.datahub_lineage_client = self._create_datahub_lineage_client()
        self.job_properties = self._parse_job_properties()
        self.object_storage = self._create_object_storage()
        self.stage_queue = self._create_stage_queue()

    def _create_datahub_lineage_client(self) -> DataHubRunTimeLineage:
        """Create DataHub runtime lineage client for this worker."""
        datahub_settings = self.runtime_context.datahub_settings
        return DataHubRunTimeLineage(
            client_config=DataHubLineageRuntimeConfig(
                connection_settings=DataHubRuntimeConnectionSettings(
                    server=datahub_settings.server,
                    env=datahub_settings.env,
                    token=datahub_settings.token,
                    timeout_sec=datahub_settings.timeout_sec,
                    retry_max_times=datahub_settings.retry_max_times,
                ),
                data_job_key=self.runtime_context.data_job_key,
            )
        )

    def _parse_job_properties(self) -> dict[str, Any]:
        """Create nested job properties from DataHub custom properties."""
        custom_properties = self.datahub_lineage_client.resolved_job_config.custom_properties
        return JobPropertiesParser(custom_properties).job_properties

    def _create_stage_queue(self) -> StageQueue:
        """Create queue gateway from job queue config."""
        queue_config = self.job_properties["job"]["queue"]
        return StageQueue(
            self.runtime_context.queue_settings.broker_url,
            queue_config=queue_config,
        )

    def _create_object_storage(self) -> ObjectStorageGateway:
        """Create object storage gateway from S3 settings."""
        return ObjectStorageGateway(
            S3Client(
                endpoint_url=self.runtime_context.s3_settings.s3_endpoint,
                access_key=self.runtime_context.s3_settings.s3_access_key,
                secret_key=self.runtime_context.s3_settings.s3_secret_key,
                region_name=self.runtime_context.s3_settings.aws_region,
            )
        )
