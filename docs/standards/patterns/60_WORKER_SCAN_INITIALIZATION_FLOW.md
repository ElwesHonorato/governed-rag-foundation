# Worker Scan Initialization Flow

This document explains `worker_scan` startup step by step, class by class, and maps each part to the design pattern being used.

## 1) Entry Point (`run`)
File: `domains/worker_scan/src/app.py`

`run()` is the composition root for this worker.

It does two things:
1. Creates `RuntimeContextFactory` with settings from env.
2. Creates `WorkerRuntimeLauncher` with worker-specific collaborators.

Code shape:
1. `RuntimeContextFactory(...)`
2. `WorkerRuntimeLauncher(...).start()`

Pattern: Composition Root
Why: concrete wiring is centralized in one place.

## 2) `RuntimeContextFactory` Assembles Shared Runtime
File: `libs/pipeline-common/src/pipeline_common/startup/runtime_factory.py`

`RuntimeContextFactory` takes:
1. `data_job_key`
2. `datahub_settings`
3. `s3_settings`
4. `queue_settings`

Then `_build_runtime_context()` does:
1. Build lineage gateway via `DataHubLineageGatewayFactory`.
2. Parse DataHub `custom_properties` into nested `job_properties` using `JobPropertiesParser`.
3. Build object storage gateway via `ObjectStorageGatewayFactory`.
4. Build stage queue gateway via `StageQueueGatewayFactory` using `job_properties["job"]["queue"]`.
5. Return `WorkerRuntimeContext`.

Pattern: Assembler / Shared Composition-Root Helper
Why: builds one reusable dependency bundle for all workers.

## 3) `WorkerRuntimeContext` Holds Dependencies
File: `libs/pipeline-common/src/pipeline_common/startup/runtime_context.py`

`WorkerRuntimeContext` is a dataclass with:
1. `lineage_gateway`
2. `object_storage_gateway`
3. `stage_queue_gateway`
4. `job_properties`

Pattern: Context Object / Parameter Object
Why: passes one dependency bundle instead of many args.

## 4) `WorkerRuntimeLauncher.start()` Orchestrates Startup
File: `libs/pipeline-common/src/pipeline_common/startup/launcher.py`

`start()` performs the fixed startup pipeline:
1. Read `runtime` from injected `runtime_factory`.
2. Build typed worker config with `config_extractor.extract(runtime.job_properties)`.
3. Build service with `service_factory.build(runtime, worker_config)`.
4. Call `service.serve()`.

Patterns:
1. Template Method (DI-based)
2. Orchestrator

Why: fixed algorithm with injected variable steps.

## 5) `ScanConfigExtractor` Converts Raw Job Config to Typed Config
File: `domains/worker_scan/src/app.py`

`ScanConfigExtractor.extract(...)`:
1. Reads `job_properties["job"]`.
2. Reads `storage` and `queue`.
3. Builds `ScanJobConfigContract`.
4. Builds `ScanQueueConfigContract`.
5. Returns `ScanWorkerConfig`.

Pattern: Translator / Adapter
Why: isolates raw dict parsing from service/runtime logic.

## 6) `ScanServiceFactory` Builds Worker Service Graph
File: `domains/worker_scan/src/app.py`

`ScanServiceFactory.build(...)`:
1. Gets gateways from `runtime`.
2. Executes startup side effect: `bootstrap_bucket_prefixes(worker_config.bucket)`.
3. Builds `StorageScanCycleProcessor` with `ScanStorageContract`.
4. Builds `WorkerScanService` with `ScanPollingContract`.
5. Returns the service.

Pattern: Factory Method / Service Assembler
Why: encapsulates creation of the service object graph.

## 7) `WorkerScanService` Runs the Loop
File: `domains/worker_scan/src/services/worker_scan_service.py`

`WorkerScanService.serve()`:
1. Infinite loop.
2. Calls `processor.scan()`.
3. Logs and continues on failure.
4. Sleeps for `poll_interval_seconds`.

Pattern: Service Loop / Polling Worker

## 8) `StorageScanCycleProcessor` Executes One Scan Cycle
File: `domains/worker_scan/src/services/scan_cycle_processor.py`

`scan()`:
1. Lists source keys from `input_prefix`.
2. Filters candidate keys.
3. For each key:
1. Starts lineage run.
2. Adds input/output lineage datasets.
3. Copies object to `output_prefix`.
4. Publishes parse message to queue.
5. Deletes source object.
6. Completes or aborts lineage run.

Pattern: Application Service / Use-Case Processor

## End-to-End Call Order
1. `run()`
2. `RuntimeContextFactory(...)`
3. `RuntimeContextFactory._build_runtime_context()`
4. `WorkerRuntimeLauncher.start()`
5. `ScanConfigExtractor.extract(...)`
6. `ScanServiceFactory.build(...)`
7. `WorkerScanService.serve()`
8. `StorageScanCycleProcessor.scan()`

## Patterns Involved

### Composition Root
Where: `worker_scan.run()`

Why: It wires concrete dependencies (`settings`, `factory`, `extractor`, `service factory`) in one place.

### Constructor Injection + Inversion of Control
Where: `WorkerRuntimeLauncher` and `RuntimeContextFactory` constructors

Why: Dependencies are provided from outside, not created ad hoc inside business code.

### Strategy
Where: `WorkerConfigExtractor` interface and `ScanConfigExtractor` implementation

Why: Config extraction behavior is swappable per worker.

### Factory Method / Service Assembler
Where: `WorkerServiceFactory` interface and `ScanServiceFactory` implementation

Why: Creates one service graph product for the worker.

### Gateway Factories (Simple Builders)
Where: `DataHubLineageGatewayFactory`, `ObjectStorageGatewayFactory`, `StageQueueGatewayFactory`

Why: Each class constructs one gateway deterministically from settings.

### Config Decoder / Dot-Notation Expander
Where: `JobPropertiesParser`

Why: Transforms flat keys (`job.storage.input_prefix`) into nested dict structure.

### Orchestrator
Where: `WorkerRuntimeLauncher.start()`

Why: It controls sequencing across factory, extractor, and service without containing domain logic.

## Mental Model
1. `run()` wires.
2. `RuntimeContextFactory` assembles infra + config.
3. `WorkerRuntimeLauncher` orchestrates startup steps.
4. `ScanConfigExtractor` translates config.
5. `ScanServiceFactory` builds runtime objects.
6. `WorkerScanService` runs forever.
7. `StorageScanCycleProcessor` does the actual unit of work.
