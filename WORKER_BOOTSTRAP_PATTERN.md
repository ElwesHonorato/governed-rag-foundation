# Worker Bootstrap Pattern (OOP, Adversarial)

## Position
If worker startup stays as free-floating functions, this repo will keep drifting.  
Use class-based startup with explicit responsibilities and hard boundaries.

## Target design (Object-Oriented)
Use these patterns together:
1. Startup Pipeline: one shared startup pipeline for all workers.
2. Abstract Factory: class-based service construction.
3. Strategy: class-based config extraction per worker.
4. Composition Root: each worker app wires one bootstrap object and calls `start()`.

References:
1. Template Method: https://refactoring.guru/design-patterns/template-method
2. Abstract Factory: https://refactoring.guru/design-patterns/abstract-factory
3. Dependency Injection/Composition Root rationale: https://martinfowler.com/articles/injection.html
4. Config separation: https://12factor.net/config
5. Google Python docstrings: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings

## Non-negotiable architecture
1. No loose startup functions in worker apps.
2. No raw `dict[str, Any]` passed to services.
3. No worker-specific orchestration logic outside a bootstrap class.
4. One property namespace only: `job.*`.

## Canonical class model
Implement in `libs/pipeline-common/src/pipeline_common/startup.py`:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Mapping, TypeVar

TConfig = TypeVar("TConfig")
TService = TypeVar("TService")

@dataclass(frozen=True)
class WorkerRuntimeContext:
    ...

class WorkerService(ABC):
    @abstractmethod
    def serve(self) -> None: ...

class WorkerConfigExtractor(ABC, Generic[TConfig]):
    @abstractmethod
    def extract(self, custom_properties: Mapping[str, str]) -> TConfig: ...

class WorkerServiceFactory(ABC, Generic[TConfig, TService]):
    @abstractmethod
    def build(self, runtime: WorkerRuntimeContext, worker_config: TConfig) -> TService: ...

class WorkerRuntimeLauncher(Generic[TConfig, TService]):
    def __init__(
        self,
        *,
        data_job_key: DataHubDataJobKey,
        config_extractor: WorkerConfigExtractor[TConfig],
        service_factory: WorkerServiceFactory[TConfig, TService],
    ) -> None:
        self._data_job_key = data_job_key
        self._config_extractor = config_extractor
        self._service_factory = service_factory

    def start(self) -> None:
        runtime_factory = RuntimeContextFactory(data_job_key=self._data_job_key)
        runtime = runtime_factory.runtime_context
        worker_config = self._config_extractor.extract(runtime.job_properties)
        service = self._service_factory.build(runtime, worker_config)
        service.serve()
```

## `job.*` standard
All governance custom properties must be flat under `job.*`:
1. `job.version`
2. `job.poll_interval_seconds`
3. `job.queue.*`
4. `job.storage.*`
5. stage-specific keys like `job.filters.*`, `job.security.*`, `job.dimension`

Do not introduce `scan.*`, `parse.*`, `job.stage.*`, or `job.runtime.*`.

## Worker implementation contract
Each worker must define:
1. `XWorkerConfig` dataclass.
2. `XConfigExtractor(WorkerConfigExtractor[XWorkerConfig])`.
3. `XServiceFactory(WorkerServiceFactory[XWorkerConfig, WorkerService])`.
4. A composition root that wires `WorkerRuntimeLauncher` with job key + extractor + factory.

Worker `app.py` should be minimal:
```python
def run() -> None:
    WorkerRuntimeLauncher[ScanWorkerConfig, WorkerScanService](
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_scan"),
        config_extractor=ScanConfigExtractor(),
        service_factory=ScanServiceFactory(),
    ).start()
```

## Migration plan for current repo
1. Keep shared env/DataHub/queue/storage resolvers in `pipeline_common.startup`.
2. Replace function hooks in `worker_scan` with concrete classes first.
3. Replicate same class structure to:
   - `worker_parse_document`
   - `worker_chunk_text`
   - `worker_embed_chunks`
   - `worker_index_weaviate`
   - `worker_manifest`
   - `worker_metrics`
4. Remove old function-based startup API after all workers migrate.

## Adversarial review gates
A PR fails if:
1. A worker app contains orchestration code not owned by a bootstrap class.
2. A service receives untyped config dictionaries.
3. Governance definitions use prefixes outside `job.*`.
4. New runtime dependency changes are merged without lock-file updates.
5. Docstrings in changed Python files are not Google-style.

## Definition of done
1. One abstract startup pipeline, reused by every worker.
2. One `job.*` config schema, consumed by typed extractors.
3. No duplicated startup sequence across worker apps.
4. End-to-end flow still works by dropping one HTML file into `rag-data/01_incoming`.
