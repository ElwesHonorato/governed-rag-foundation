"""Worker runtime launcher orchestration."""

from typing import Generic

from pipeline_common.lineage.contracts import DataHubDataJobKey
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
        data_job_key: DataHubDataJobKey,
        config_extractor: WorkerConfigExtractor[TWorkerConfig],
        service_factory: WorkerServiceFactory[TWorkerConfig, TWorkerService],
    ) -> None:
        self._data_job_key = data_job_key
        self._config_extractor = config_extractor
        self._service_factory = service_factory

    def start(self) -> None:
        """Execute the standard worker startup pipeline."""
        runtime_factory = RuntimeContextFactory(data_job_key=self._data_job_key)
        runtime = runtime_factory.runtime_context
        worker_config = self._config_extractor.extract(runtime.job_properties)
        service = self._service_factory.build(runtime, worker_config)
        service.serve()
