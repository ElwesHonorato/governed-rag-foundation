"""Capability-scoped runtime settings provider.

Layer:
- Infrastructure configuration adapter used by composition roots.

Role:
- Convert environment variables into typed settings objects requested by a
  worker/app startup path.

Design intent:
- Keep env parsing logic out of service and gateway construction code.
- Allow startup paths to request only needed capabilities.

Non-goals:
- This module does not validate cross-capability consistency.
- This module does not own business defaults beyond env parsing defaults.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline_common.helpers.config import _optional_env
from pipeline_common.gateways.lineage.settings import DataHubSettings
from pipeline_common.gateways.object_storage.settings import S3StorageSettings
from pipeline_common.gateways.queue.settings import QueueRuntimeSettings


@dataclass(frozen=True)
class DBSettings:
    """Placeholder DB settings contract (not implemented in this repository)."""


@dataclass(frozen=True)
class CacheSettings:
    """Placeholder cache settings contract (not implemented in this repository)."""


@dataclass(frozen=True)
class SparkSettings:
    """Spark runtime settings for workers."""

    enabled: bool
    master_url: str
    app_name: str


StorageSettings = S3StorageSettings
QueueSettings = QueueRuntimeSettings


@dataclass(frozen=True)
class SettingsRequest:
    """Requested capability settings to load from environment."""

    db: bool = False
    storage: bool = False
    queue: bool = False
    datahub: bool = False
    cache: bool = False
    spark: bool = False


@dataclass(frozen=True)
class SettingsBundle:
    """Bundle of loaded settings based on a requested capability set."""

    db: DBSettings | None = None
    storage: StorageSettings | None = None
    queue: QueueSettings | None = None
    datahub: DataHubSettings | None = None
    cache: CacheSettings | None = None
    spark: SparkSettings | None = None


def load_db_settings_from_env() -> DBSettings:
    """Load DB settings from environment."""
    raise NotImplementedError("DB settings loader is not implemented yet.")


def load_storage_settings_from_env() -> StorageSettings:
    """Load object storage settings from environment."""
    return S3StorageSettings.from_env()


def load_queue_settings_from_env() -> QueueSettings:
    """Load queue settings from environment."""
    return QueueRuntimeSettings.from_env()


def load_datahub_settings_from_env() -> DataHubSettings:
    """Load DataHub settings from environment."""
    return DataHubSettings.from_env()


def load_cache_settings_from_env() -> CacheSettings:
    """Load cache settings from environment."""
    raise NotImplementedError("Cache settings loader is not implemented yet.")


def load_spark_settings_from_env() -> SparkSettings:
    """Load Spark settings from environment."""
    enabled_raw = _optional_env("SPARK_ENABLED", "false").lower()
    enabled = enabled_raw in {"1", "true", "yes", "on"}
    return SparkSettings(
        enabled=enabled,
        master_url=_optional_env("SPARK_MASTER_URL", "local[*]"),
        app_name=_optional_env("SPARK_APP_NAME", "worker-process"),
    )


class SettingsProvider:
    """Load requested capability settings from environment variables.

    Layer:
    - Infrastructure configuration adapter.

    Dependencies:
    - Gateway-specific settings loaders.
    - Process environment.

    Design intent:
    - Keep composition roots declarative by requesting capabilities, then
      consuming a typed bundle.

    Non-goals:
    - Avoids caching policy beyond returning a snapshot in ``bundle``.
    - Does not perform service wiring; only settings loading.
    """

    def __init__(self, request: SettingsRequest) -> None:
        self._request = request

    @property
    def db(self) -> DBSettings | None:
        """Load DB settings when requested."""
        if not self._request.db:
            return None
        return load_db_settings_from_env()

    @property
    def storage(self) -> StorageSettings | None:
        """Load object storage settings when requested."""
        if not self._request.storage:
            return None
        return load_storage_settings_from_env()

    @property
    def queue(self) -> QueueSettings | None:
        """Load queue settings when requested."""
        if not self._request.queue:
            return None
        return load_queue_settings_from_env()

    @property
    def datahub(self) -> DataHubSettings | None:
        """Load DataHub settings when requested."""
        if not self._request.datahub:
            return None
        return load_datahub_settings_from_env()

    @property
    def cache(self) -> CacheSettings | None:
        """Load cache settings when requested."""
        if not self._request.cache:
            return None
        return load_cache_settings_from_env()

    @property
    def spark(self) -> SparkSettings | None:
        """Load spark settings when requested."""
        if not self._request.spark:
            return None
        return load_spark_settings_from_env()

    @property
    def bundle(self) -> SettingsBundle:
        """Return the loaded settings bundle."""
        return SettingsBundle(
            db=self.db,
            storage=self.storage,
            queue=self.queue,
            datahub=self.datahub,
            cache=self.cache,
            spark=self.spark,
        )
