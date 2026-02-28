"""Typed startup contracts for worker_index_weaviate."""

from dataclasses import dataclass


@dataclass(frozen=True)
class IndexWeaviateQueueConfigContract:
    """Typed contract for index_weaviate queue runtime settings."""

    stage: str
    queue_pop_timeout_seconds: int
    pop_timeout_seconds: int
    consume: str
    dlq: str


@dataclass(frozen=True)
class IndexWeaviateJobConfigContract:
    """Typed contract for index_weaviate storage/runtime fields."""

    bucket: str
    input_prefix: str
    output_prefix: str
    poll_interval_seconds: int


@dataclass(frozen=True)
class IndexWeaviateStorageConfigContract:
    """Typed storage contract for index_weaviate processing runtime."""

    bucket: str
    input_prefix: str
    output_prefix: str


@dataclass(frozen=True)
class IndexWeaviateProcessingConfigContract:
    """Typed processing runtime contract consumed by index_weaviate service."""

    poll_interval_seconds: int
    queue: IndexWeaviateQueueConfigContract
    storage: IndexWeaviateStorageConfigContract


@dataclass(frozen=True)
class IndexWeaviateWorkerConfig:
    """Typed index_weaviate worker startup configuration."""

    bucket: str
    input_prefix: str
    output_prefix: str
    poll_interval_seconds: int
    queue_config: IndexWeaviateQueueConfigContract
