"""Startup-specific contracts for worker_scan."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ScanStorageContract:
    """Storage bucket and stage prefix settings for scan worker."""

    bucket: str
    source_prefix: str
    output_prefix: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ScanStorageContract:
        """Build scan storage config from a dictionary payload."""
        return cls(**payload)


@dataclass(frozen=True)
class RawScanJobConfig:
    """Raw scan job config parsed directly from job properties."""

    storage: ScanStorageContract
    poll_interval_seconds: int

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RawScanJobConfig:
        """Build raw scan job config from a dictionary payload."""
        return cls(
            storage=ScanStorageContract.from_dict(payload["storage"]),
            poll_interval_seconds=int(payload["poll_interval_seconds"]),
        )


@dataclass(frozen=True)
class RuntimeScanJobConfig:
    """Runtime scan job config consumed by service wiring."""

    storage: ScanStorageContract
    poll_interval_seconds: int
