"""Shared worker startup helpers.

These utilities keep worker entrypoints orchestration-focused while
reusing common bootstrapping patterns across workers.
"""

from typing import Any, Mapping

from pipeline_common.lineage.contracts import DataHubDataJobKey
from pipeline_common.lineage import LineageEmitter, LineageEmitterConfig
from pipeline_common.lineage.data_hub import DataHubRunTimeLineage
from pipeline_common.lineage.data_hub.contracts import DataHubLineageRuntimeConfig
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.queue import StageQueue
from pipeline_common.settings import (
    DataHubBootstrapSettings,
    LineageEmitterSettings,
    QueueRuntimeSettings,
    S3StorageSettings,
)


def load_runtime_settings() -> tuple[S3StorageSettings, QueueRuntimeSettings, DataHubBootstrapSettings]:
    """Load environment-backed runtime settings."""
    return (
        S3StorageSettings.from_env(),
        QueueRuntimeSettings.from_env(),
        DataHubBootstrapSettings.from_env(),
    )


def load_storage_settings() -> S3StorageSettings:
    """Load S3 storage settings from environment."""
    return S3StorageSettings.from_env()


def load_worker_runtime_settings() -> tuple[S3StorageSettings, QueueRuntimeSettings, LineageEmitterSettings]:
    """Load environment-backed runtime settings for workers using LineageEmitter."""
    return (
        S3StorageSettings.from_env(),
        QueueRuntimeSettings.from_env(),
        LineageEmitterSettings.from_env(),
    )


def build_datahub_lineage_client(
    *,
    datahub_settings: DataHubBootstrapSettings,
    data_job_key: DataHubDataJobKey,
) -> DataHubRunTimeLineage:
    """Build DataHub lineage client for one worker."""
    return DataHubRunTimeLineage(
        client_config=DataHubLineageRuntimeConfig(
            bootstrap_settings={
                "server": datahub_settings.server,
                "env": datahub_settings.env,
                "token": datahub_settings.token,
            },
            data_job_key=data_job_key,
        )
    )


def build_lineage_emitter(
    *,
    lineage_settings: LineageEmitterSettings,
    lineage_config: LineageEmitterConfig,
) -> LineageEmitter:
    """Build lineage emitter for one worker."""
    return LineageEmitter(
        lineage_settings=lineage_settings,
        lineage_config=lineage_config,
    )


def set_nested(target: dict[str, Any], dotted_key: str, value: str) -> None:
    """Set one dotted key (for example, 'scan.storage.bucket') into nested dict."""
    cursor: dict[str, Any] = target
    parts = dotted_key.split(".")
    for part in parts[:-1]:
        cursor = cursor.setdefault(part, {})
    cursor[parts[-1]] = value


def expand_dot_properties(custom_properties: Mapping[str, str]) -> dict[str, Any]:
    """Expand dot-notation custom properties into a nested mapping."""
    expanded: dict[str, Any] = {}
    for key, value in custom_properties.items():
        if "." in key:
            set_nested(expanded, key, value)
    return expanded


def parse_csv_list(value: Any) -> list[str]:
    """Parse comma-separated string into normalized list."""
    return [item.strip() for item in str(value).split(",") if item.strip()]


def build_stage_queue(*, broker_url: str, queue_config: dict[str, Any]) -> StageQueue:
    """Build queue gateway for one worker."""
    return StageQueue(
        broker_url,
        queue_config=queue_config,
    )


def build_object_storage(s3_settings: S3StorageSettings) -> ObjectStorageGateway:
    """Build object storage gateway from S3 settings."""
    return ObjectStorageGateway(
        S3Client(
            endpoint_url=s3_settings.s3_endpoint,
            access_key=s3_settings.s3_access_key,
            secret_key=s3_settings.s3_secret_key,
            region_name=s3_settings.aws_region,
        )
    )
