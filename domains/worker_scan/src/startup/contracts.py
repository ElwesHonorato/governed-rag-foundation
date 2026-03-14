"""Startup-specific contracts for worker_scan."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RawScanStorageConfig:
    """Storage bucket and stage prefix settings from job properties."""

    bucket: str
    source_prefix: str
    output_prefix: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RawScanStorageConfig:
        """Build scan storage config from a dictionary payload."""
        source_prefix = payload.get("source_prefix", payload.get("input_prefix"))
        if source_prefix is None:
            raise KeyError("source_prefix")
        return cls(
            bucket=str(payload["bucket"]),
            source_prefix=str(source_prefix),
            output_prefix=str(payload["output_prefix"]),
        )


@dataclass(frozen=True)
class RuntimeScanStorageConfig:
    """Runtime storage config consumed by the scan worker."""

    bucket: str
    source_prefix: str
    output_prefix: str

    @classmethod
    def from_raw(
        cls,
        raw: RawScanStorageConfig,
        *,
        env: str | None,
    ) -> RuntimeScanStorageConfig:
        """Build runtime storage config from raw startup config."""
        return cls(
            bucket=raw.bucket,
            source_prefix=f"{env}/{raw.source_prefix}",
            output_prefix=f"{env}/{raw.output_prefix}",
        )


@dataclass(frozen=True)
class RawScanJobConfig:
    """Raw scan job config parsed directly from job properties."""

    storage: RawScanStorageConfig
    poll_interval_seconds: int

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RawScanJobConfig:
        """Build raw scan job config from a dictionary payload."""
        return cls(
            storage=RawScanStorageConfig.from_dict(payload["storage"]),
            poll_interval_seconds=int(payload["poll_interval_seconds"]),
        )


@dataclass(frozen=True)
class RuntimeScanJobConfig:
    """Runtime scan job config consumed by service wiring."""

    storage: RuntimeScanStorageConfig
    poll_interval_seconds: int
