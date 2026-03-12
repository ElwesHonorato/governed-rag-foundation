from __future__ import annotations

from dataclasses import dataclass

from startup.contracts import RuntimeScanStorageConfig


@dataclass(frozen=True)
class ScanWorkItem:
    """One source-to-destination promotion planned by the scan processor."""

    source_key: str
    destination_key: str


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

    def plan_work(self, keys: list[str]) -> list[ScanWorkItem]:
        """Plan source objects that should be promoted this cycle."""
        return [
            ScanWorkItem(
                source_key=key,
                destination_key=self.destination_key(key),
            )
            for key in keys
            if self.is_candidate_key(key)
        ]

    def is_candidate_key(self, key: str) -> bool:
        """Return True when a key is a processable source object."""
        return key.startswith(self._source_prefix) and key != self._source_prefix

    def destination_key(self, source_key: str) -> str:
        """Map a source key to its destination key."""
        return source_key.replace(self._source_prefix, self._destination_prefix, 1)
