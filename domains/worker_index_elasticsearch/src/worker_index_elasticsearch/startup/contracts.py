"""Startup-specific contracts for worker_index_elasticsearch."""

from __future__ import annotations

import os
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
    elasticsearch_url: str
    elasticsearch_index: str

    @classmethod
    def from_raw(
        cls,
        raw: RawIndexElasticsearchJobConfig,
    ) -> "RuntimeIndexElasticsearchJobConfig":
        """Build runtime config from raw job properties and environment."""
        elasticsearch_url = os.environ.get("ELASTICSEARCH_URL", "").strip()
        if not elasticsearch_url:
            raise ValueError("ELASTICSEARCH_URL is not configured")
        elasticsearch_index = os.environ.get("ELASTICSEARCH_INDEX", "rag_chunks").strip()
        return cls(
            poll_interval_seconds=raw.poll_interval_seconds,
            elasticsearch_url=elasticsearch_url,
            elasticsearch_index=elasticsearch_index,
        )
