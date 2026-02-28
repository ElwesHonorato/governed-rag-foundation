"""Startup contracts shared by worker entrypoints."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, Mapping, TypeVar

from pipeline_common.startup.runtime_context import WorkerRuntimeContext

TWorkerConfig = TypeVar("TWorkerConfig")
TWorkerService = TypeVar("TWorkerService", bound="WorkerService")


class WorkerService(ABC):
    """Long-running worker contract."""

    @abstractmethod
    def serve(self) -> None:
        """Start serving worker loop."""


class WorkerConfigExtractor(Generic[TWorkerConfig], ABC):
    """Extractor contract for typed worker config."""

    @abstractmethod
    def extract(self, job_properties: Mapping[str, Any]) -> TWorkerConfig:
        """Parse and validate resolved worker job properties."""


class WorkerServiceFactory(Generic[TWorkerConfig, TWorkerService], ABC):
    """Factory contract for worker service construction."""

    @abstractmethod
    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: TWorkerConfig,
    ) -> TWorkerService:
        """Build worker service from runtime context + typed config."""


@dataclass(frozen=True)
class WorkerPollingContract:
    """Polling cadence contract for long-running worker loops."""

    poll_interval_seconds: int
