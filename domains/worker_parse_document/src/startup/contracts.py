"""Startup-specific contracts for worker_parse_document."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RawParseStorageConfig:
    """Storage config declared in job properties."""

    bucket: str
    output_prefix: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RawParseStorageConfig:
        """Build parse storage config from a dictionary payload."""
        return cls(
            bucket=str(payload["bucket"]),
            output_prefix=str(payload["output_prefix"]),
        )


@dataclass(frozen=True)
class RuntimeParseStorageConfig:
    """Runtime storage config consumed by the parse worker."""

    bucket: str
    output_prefix: str

    @classmethod
    def from_raw(
        cls,
        raw: RawParseStorageConfig,
        *,
        env: str | None,
    ) -> RuntimeParseStorageConfig:
        """Build runtime storage config from raw startup config."""
        return cls(
            bucket=raw.bucket,
            output_prefix=f"{env}/{raw.output_prefix}",
        )


@dataclass(frozen=True)
class RuntimeParseSecurityConfig:
    """Typed security contract for parse processing runtime."""

    clearance: str


@dataclass(frozen=True)
class RawParseJobConfig:
    """Raw parse job config parsed directly from job properties."""

    storage: RawParseStorageConfig
    poll_interval_seconds: int
    security_clearance: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RawParseJobConfig:
        """Build raw parse job config from a dictionary payload."""
        return cls(
            storage=RawParseStorageConfig.from_dict(payload["storage"]),
            poll_interval_seconds=int(payload["poll_interval_seconds"]),
            security_clearance=str(payload["security"]["clearance"]),
        )


@dataclass(frozen=True)
class RuntimeParseJobConfig:
    """Runtime parse job config after startup-time shaping."""

    storage: RuntimeParseStorageConfig
    poll_interval_seconds: int
    security: RuntimeParseSecurityConfig
