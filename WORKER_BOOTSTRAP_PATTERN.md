# Worker Bootstrap Pattern (OOP, Adversarial)

## Position
If worker startup stays as free-floating functions, this repo will keep drifting.  
Use class-based startup with explicit responsibilities and hard boundaries.

## Target design (Object-Oriented)
Use these patterns together:
1. Template Method: one abstract startup pipeline for all workers.
2. Abstract Factory: class-based service construction.
3. Strategy: class-based config extraction per worker.
4. Composition Root: each worker app wires one bootstrap object and calls `run()`.

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

class WorkerBootstrap(ABC, Generic[TConfig, TService]):
    def run(self) -> None:
        # template method: fixed orchestration
        runtime = self._resolve_runtime()
        worker_config = self.extractor().extract(runtime.lineage.resolved_job_config.custom_properties)
        service = self.factory().build(runtime, worker_config)
        service.serve()

    @abstractmethod
    def extractor(self) -> WorkerConfigExtractor[TConfig]: ...

    @abstractmethod
    def factory(self) -> WorkerServiceFactory[TConfig, TService]: ...

    @abstractmethod
    def _resolve_runtime(self) -> WorkerRuntimeContext: ...
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
4. `XWorkerBootstrap(WorkerBootstrap[XWorkerConfig, WorkerService])`.

Worker `app.py` should be minimal:
```python
def run() -> None:
    ScanWorkerBootstrap().run()
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
