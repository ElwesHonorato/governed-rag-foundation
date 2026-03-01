"""Typed startup contracts for worker_scan."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScanQueueConfigContract:
    """Typed contract for scan queue runtime settings."""

    stage: str
    queue_pop_timeout_seconds: int
    pop_timeout_seconds: int
    produce: str
    dlq: str
    consume: str = ""


@dataclass(frozen=True)
class ScanJobConfigContract:
    """Typed contract for scan-specific job config fields."""

    bucket: str
    input_prefix: str
    output_prefix: str
    poll_interval_seconds: int


@dataclass(frozen=True)
class ScanStorageContract:
    """Storage bucket and stage prefix settings for scan worker."""

    bucket: str
    input_prefix: str
    output_prefix: str


@dataclass(frozen=True)
class ScanWorkerConfigContract:
    """Typed scan worker startup configuration."""

    storage: ScanStorageContract
    poll_interval_seconds: int
    queue_config: ScanQueueConfigContract
