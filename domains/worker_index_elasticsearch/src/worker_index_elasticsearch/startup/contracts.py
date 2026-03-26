"""Startup-specific contracts for worker_index_elasticsearch."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RawIndexElasticsearchJobConfig:
    """Raw worker config parsed directly from job properties."""

    poll_interval_seconds: int

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RawIndexElasticsearchJobConfig":
        """Build raw worker config from a dictionary payload."""
        return cls(
            poll_interval_seconds=int(payload["poll_interval_seconds"]),
        )


@dataclass(frozen=True)
class RuntimeIndexElasticsearchJobConfig:
    """Runtime config consumed by the worker service graph."""

    poll_interval_seconds: int

    @classmethod
    def from_raw(
        cls,
        raw: RawIndexElasticsearchJobConfig,
    ) -> "RuntimeIndexElasticsearchJobConfig":
        """Build runtime config from raw job properties."""
        return cls(
            poll_interval_seconds=raw.poll_interval_seconds,
        )
