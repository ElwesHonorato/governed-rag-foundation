"""Worker runtime launcher orchestration."""

from typing import Generic

from pipeline_common.startup.contracts import (
    TWorkerConfig,
    TWorkerService,
    WorkerConfigExtractor,
    WorkerServiceFactory,
)
from pipeline_common.startup.runtime_factory import RuntimeContextFactory


class WorkerRuntimeLauncher(Generic[TWorkerConfig, TWorkerService]):
    """Launch worker runtime from injected startup collaborators."""

    def __init__(
        self,
        *,
        runtime_factory: RuntimeContextFactory,
        config_extractor: WorkerConfigExtractor[TWorkerConfig],
        service_factory: WorkerServiceFactory[TWorkerConfig, TWorkerService],
    ) -> None:
        self._runtime_factory = runtime_factory
        self._config_extractor = config_extractor
        self._service_factory = service_factory

    def start(self) -> None:
        """Execute the standard worker startup pipeline."""
        runtime = self._runtime_factory.runtime_context
        worker_config = self._config_extractor.extract(runtime.job_properties)
        service = self._service_factory.build(runtime, worker_config)
        service.serve()
