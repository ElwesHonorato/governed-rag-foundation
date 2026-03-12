# Worker Bootstrap Pattern (OOP, Adversarial)

## Position
Worker startup should stay explicit and typed, but the composition root does not need a dedicated launcher class.

## Target design (Object-Oriented)
Use these patterns together:
1. Shared bootstrap contracts: one shared bootstrap shape for all workers.
2. Abstract Factory: class-based service construction.
3. Strategy: class-based config extraction per worker.
4. Composition Root: each worker app wires runtime context, extractor, and service factory directly.

References:
1. Template Method: https://refactoring.guru/design-patterns/template-method
2. Abstract Factory: https://refactoring.guru/design-patterns/abstract-factory
3. Dependency Injection/Composition Root rationale: https://martinfowler.com/articles/injection.html
4. Config separation: https://12factor.net/config
5. Google Python docstrings: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings

## Non-negotiable architecture
1. No ad hoc startup logic spread across multiple files.
2. No raw `dict[str, Any]` passed to services.
3. No worker-specific orchestration logic outside the composition root and worker startup collaborators.
4. One property namespace only: `job.*`.

## Canonical class model
Implement shared contracts in `libs/pipeline-common/src/pipeline_common/startup/`:

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
4. A composition root that wires runtime context, extractor, and service factory.

Worker `app.py` should be minimal:
```python
def run() -> None:
    runtime_context = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_scan"),
        settings_bundle=settings,
    ).build()
    worker_config = ScanConfigExtractor().extract(runtime_context.job_properties)
    service = ScanServiceFactory().build(runtime_context, worker_config)
    service.serve()
```

## Migration plan for current repo
1. Keep shared env/DataHub/queue/storage resolvers in `pipeline_common.startup`.
2. Keep typed extractor and service factory classes per worker.
3. Replicate the same composition-root shape across:
   - `worker_parse_document`
   - `worker_chunk_text`
   - `worker_embed_chunks`
   - `worker_index_weaviate`
4. Keep startup steps explicit in `app.py`.

## Adversarial review gates
A PR fails if:
1. A worker app contains startup logic that leaks business behavior into `app.py`.
2. A service receives untyped config dictionaries.
3. Governance definitions use prefixes outside `job.*`.
4. New runtime dependency changes are merged without lock-file updates.
5. Docstrings in changed Python files are not Google-style.

## Definition of done
1. One explicit startup shape, reused by every worker.
2. One `job.*` config schema, consumed by typed extractors.
3. No drift in startup sequencing across worker apps.
4. End-to-end flow still works by dropping one HTML file into `rag-data/01_incoming`.
