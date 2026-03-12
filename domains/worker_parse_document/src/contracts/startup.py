"""Startup-specific contracts for worker_parse_document."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParseStorageConfigContract:
    """Typed storage contract for parse processing runtime."""

    bucket: str
    output_prefix: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ParseStorageConfigContract:
        """Build parse storage config from a dictionary payload."""
        return cls(**payload)


@dataclass(frozen=True)
class ParseSecurityConfigContract:
    """Typed security contract for parse processing runtime."""

    clearance: str


@dataclass(frozen=True)
class RawParseJobConfig:
    """Raw parse job config parsed directly from job properties."""

    storage: ParseStorageConfigContract
    poll_interval_seconds: int
    security_clearance: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RawParseJobConfig:
        """Build raw parse job config from a dictionary payload."""
        return cls(
            storage=ParseStorageConfigContract.from_dict(payload["storage"]),
            poll_interval_seconds=int(payload["poll_interval_seconds"]),
            security_clearance=str(payload["security"]["clearance"]),
        )


@dataclass(frozen=True)
class RuntimeParseJobConfig:
    """Runtime parse job config after startup-time shaping."""

    storage: ParseStorageConfigContract
    poll_interval_seconds: int
    security: ParseSecurityConfigContract
