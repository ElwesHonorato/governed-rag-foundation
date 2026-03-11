"""Worker startup pipeline launcher.

Layer:
- Startup/application orchestration.

Role:
- Execute the standard startup sequence:
  runtime context -> typed config extraction -> service construction -> serve.

Design intent:
- Keep worker entrypoints thin while enforcing a consistent bootstrap flow.

Non-goals:
- Does not own worker-specific configuration parsing rules.
- Does not own worker processing logic.
"""

from typing import Generic

from pipeline_common.gateways.processing_engine import stop_spark_session
from pipeline_common.startup.contracts import (
    TWorkerConfig,
    TWorkerService,
    WorkerConfigExtractor,
    WorkerServiceFactory,
)
from pipeline_common.startup.runtime_context import WorkerRuntimeContext


class WorkerRuntimeLauncher(Generic[TWorkerConfig, TWorkerService]):
    """Orchestrate worker bootstrap from injected startup collaborators.

    Layer:
    - Startup orchestration.

    Dependencies:
    - Runtime context.
    - Worker-specific config extractor and service factory implementations.

    Design intent:
    - Provide one generic launch path across worker domains.
    """

    def __init__(
        self,
        *,
        runtime_context: WorkerRuntimeContext,
        config_extractor: WorkerConfigExtractor[TWorkerConfig],
        service_factory: WorkerServiceFactory[TWorkerConfig, TWorkerService],
    ) -> None:
        self._runtime_context = runtime_context
        self._config_extractor = config_extractor
        self._service_factory = service_factory

    def start(self) -> None:
        """Execute the standard worker startup pipeline."""
        try:
            worker_config = self._config_extractor.extract(self._runtime_context.job_properties)
            service = self._service_factory.build(self._runtime_context, worker_config)
            service.serve()
        finally:
            stop_spark_session(self._runtime_context.spark_session)
