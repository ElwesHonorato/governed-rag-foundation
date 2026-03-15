from __future__ import annotations

from dataclasses import dataclass

from worker_scan.startup.contracts import RuntimeScanStorageConfig


@dataclass(frozen=True)
class ScanWorkItem:
    """One source-to-destination promotion planned by the scan processor."""

    source_uri: str
    destination_uri: str


class StorageScanCycleProcessor:
    """Build scan decisions for source->destination promotion."""

    def __init__(
        self,
        *,
        storage_config: RuntimeScanStorageConfig,
    ) -> None:
        """Initialize instance state and dependencies."""
        self._bucket = storage_config.bucket
        self._source_prefix = storage_config.source_prefix
        self._destination_prefix = storage_config.output_prefix

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def source_prefix(self) -> str:
        return self._source_prefix

    @property
    def destination_prefix(self) -> str:
        return self._destination_prefix

    def destination_key(self, source_key: str) -> str:
        """Map a source key to its destination key."""
        return source_key.replace(self._source_prefix, self._destination_prefix, 1)
