"""Typed startup contracts for worker_parse_document."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ParseQueueConfigContract:
    """Typed contract for parse queue runtime settings."""

    stage: str
    queue_pop_timeout_seconds: int
    pop_timeout_seconds: int
    consume: str
    produce: str
    dlq: str


@dataclass(frozen=True)
class ParseJobConfigContract:
    """Typed contract for parse storage/runtime fields."""

    bucket: str
    input_prefix: str
    output_prefix: str
    poll_interval_seconds: int
    security_clearance: str


@dataclass(frozen=True)
class ParseStorageConfigContract:
    """Typed storage contract for parse processing runtime."""

    bucket: str
    input_prefix: str
    output_prefix: str


@dataclass(frozen=True)
class ParseSecurityConfigContract:
    """Typed security contract for parse processing runtime."""

    clearance: str


@dataclass(frozen=True)
class ParseProcessingConfigContract:
    """Typed processing runtime contract consumed by parse service."""

    poll_interval_seconds: int
    queue: ParseQueueConfigContract
    storage: ParseStorageConfigContract
    security: ParseSecurityConfigContract


@dataclass(frozen=True)
class ParseWorkerConfig:
    """Typed parse worker startup configuration."""

    bucket: str
    input_prefix: str
    output_prefix: str
    poll_interval_seconds: int
    security_clearance: str
    queue_config: ParseQueueConfigContract
