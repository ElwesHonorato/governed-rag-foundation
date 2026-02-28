from __future__ import annotations

from dataclasses import dataclass

from pipeline_common.gateways.lineage.settings import DataHubSettings
from pipeline_common.gateways.object_storage.settings import S3StorageSettings
from pipeline_common.gateways.queue.settings import QueueRuntimeSettings


@dataclass(frozen=True)
class DBSettings:
    """Placeholder DB settings contract (not implemented in this repository)."""


@dataclass(frozen=True)
class CacheSettings:
    """Placeholder cache settings contract (not implemented in this repository)."""


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


@dataclass(frozen=True)
class SettingsBundle:
    """Bundle of loaded settings based on a requested capability set."""

    db: DBSettings | None = None
    storage: StorageSettings | None = None
    queue: QueueSettings | None = None
    datahub: DataHubSettings | None = None
    cache: CacheSettings | None = None


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


class SettingsProvider:
    """Load capability settings from env based on a ``SettingsRequest``."""

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
    def bundle(self) -> SettingsBundle:
        """Return the loaded settings bundle."""
        return SettingsBundle(
            db=self.db,
            storage=self.storage,
            queue=self.queue,
            datahub=self.datahub,
            cache=self.cache,
        )
