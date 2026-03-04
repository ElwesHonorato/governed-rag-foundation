# Spark Migration Analysis and Implementation Plan

This document analyzes the current worker runtime architecture and provides an incremental migration plan to introduce Spark as the worker processing engine.

Scope followed:
- Analysis only (no source changes implemented).
- Grounded in repository code and `docs/ARCHITECTURE.md`.
- Divergences between documented architecture and implementation are explicitly called out.

---

## 1) Current Worker Architecture

### 1.1 Worker Entrypoints

Worker composition roots are:
- `domains/worker_scan/src/app.py`
- `domains/worker_parse_document/src/app.py`
- `domains/worker_chunk_text/src/app.py`
- `domains/worker_embed_chunks/src/app.py`
- `domains/worker_index_weaviate/src/app.py`
- `domains/worker_manifest/src/app.py`
- `domains/worker_metrics/src/app.py`

All entrypoints follow the same startup pattern:
1. Load runtime settings (`SettingsProvider(SettingsRequest(...)).bundle`).
2. Build runtime context (`RuntimeContextFactory`).
3. Launch startup pipeline (`WorkerRuntimeLauncher`).

```text
Evidence
- domains/worker_scan/src/app.py
- domains/worker_parse_document/src/app.py
- domains/worker_chunk_text/src/app.py
- domains/worker_embed_chunks/src/app.py
- domains/worker_index_weaviate/src/app.py
- domains/worker_manifest/src/app.py
- domains/worker_metrics/src/app.py
```

### 1.2 How Workers Are Launched

Operational launch is via stack scripts and per-domain compose files:
- `./stack.sh up <domain>` delegates to `tooling/ops/cmd/up.sh`.
- Compose invocation is centralized in `tooling/ops/lib/compose.sh`.
- Worker Dockerfiles run `poetry run python -m app`.

```text
Evidence
- stack.sh
- tooling/ops/cmd/up.sh
- tooling/ops/lib/compose.sh
- tooling/ops/lib/core.sh
- domains/worker_*/docker-compose.yml
- domains/worker_*/Dockerfile
```

### 1.3 Mapping Entrypoints to ARCHITECTURE.md Layers

Documented layering in `docs/ARCHITECTURE.md` maps to implementation as follows:

- Composition root:
  - `domains/worker_*/src/app.py`
- Startup wiring:
  - `libs/pipeline-common/src/pipeline_common/startup/*`
- Infrastructure adapters:
  - `libs/pipeline-common/src/pipeline_common/gateways/*`
- Config adapter:
  - `libs/pipeline-common/src/pipeline_common/settings/provider.py`
- Domain processing logic:
  - `domains/worker_*/src/services/*`
  - `domains/worker_parse_document/src/parsing/*`
  - `domains/worker_chunk_text/src/chunking/domain/text_chunker.py`

This aligns with the intended architecture model.

### 1.4 Runtime Lifecycle (Startup -> Run -> Shutdown)

Startup path (shared):
- `SettingsProvider` resolves env settings.
- `RuntimeContextFactory` builds lineage/object-storage/queue gateways and parses DataHub custom properties.
- `WorkerRuntimeLauncher.start()` extracts worker config, builds service, then calls `service.serve()`.

Run path:
- `serve()` methods are infinite loops.
- Queue workers call `stage_queue.pop_message()`; polling workers iterate storage and sleep.

Shutdown path:
- No explicit graceful shutdown hooks in workers/startup launcher.
- Lifecycle termination is delegated to process/container runtime.

```text
Evidence
- libs/pipeline-common/src/pipeline_common/settings/provider.py
- libs/pipeline-common/src/pipeline_common/startup/runtime_factory.py
- libs/pipeline-common/src/pipeline_common/startup/launcher.py
- domains/worker_*/src/services/*.py
```

### 1.5 Composition Roots, Factories, and Dependency Wiring

Shared startup contracts:
- `WorkerConfigExtractor`
- `WorkerServiceFactory`
- `WorkerService`
- `WorkerPollingContract`

Worker-specific wiring:
- `domains/worker_*/src/startup/config_extractor.py`
- `domains/worker_*/src/startup/service_factory.py`

Notable startup side effects during wiring:
- DataHub metadata resolution in lineage gateway factory.
- AMQP connection establishment in `StageQueue.__init__`.
- S3 bucket/prefix bootstrap in scan service factory.
- Weaviate schema initialization in index service factory.

```text
Evidence
- libs/pipeline-common/src/pipeline_common/startup/contracts.py
- libs/pipeline-common/src/pipeline_common/gateways/factories/lineage_gateway_factory.py
- libs/pipeline-common/src/pipeline_common/gateways/queue/queue.py
- domains/worker_scan/src/startup/service_factory.py
- domains/worker_index_weaviate/src/startup/service_factory.py
```

---

## 2) Runtime Flow

### 2.1 End-to-End Unit-of-Work Flow (Current)

Pipeline sequence:
1. `worker_scan`: move object `01_incoming/ -> 02_raw/`, enqueue parse request.
2. `worker_parse_document`: read raw object, parse content, write `03_processed/*.json`, enqueue chunk request.
3. `worker_chunk_text`: read processed JSON, split text, write `04_chunks/<doc>/<chunk>.chunk.json`, enqueue embed request(s).
4. `worker_embed_chunks`: read chunk JSON, create deterministic vector, write `05_embeddings/<doc>/<chunk>.embedding.json`, enqueue index request.
5. `worker_index_weaviate`: read embedding JSON, upsert into Weaviate, write `06_indexes/*.indexed.json`.
6. `worker_manifest` and `worker_metrics`: poll storage and emit derived artifacts/counters.

Configuration source:
- Runtime `job.*` properties are loaded from DataHub custom properties and parsed via dot-notation parser.

### 2.2 Queue and Acknowledgement Semantics

Current acknowledgement is **early ack on pop**:
- Message is acknowledged in `StageQueue._consume` immediately after `basic_get`, before downstream processing success.
- This gives at-most-once behavior at queue layer; failure handling relies on worker-level DLQ pushes/logging.

```text
Evidence
- libs/pipeline-common/src/pipeline_common/gateways/queue/queue.py
- domains/worker_*/src/services/*.py
```

### 2.3 Text-Based Flow Diagram

```text
[Container start]
  -> python -m app (worker domain)
  -> app.py composition root
  -> SettingsProvider(SettingsRequest(datahub, storage, queue)).bundle
  -> RuntimeContextFactory(data_job_key, settings_bundle)
       -> DataHubLineageGatewayFactory.build() + resolve_job_metadata()
       -> JobPropertiesParser(custom_properties -> nested job config)
       -> ObjectStorageGatewayFactory.build()
       -> StageQueueGatewayFactory.build(queue_config from job properties)
  -> WorkerRuntimeLauncher.start()
       -> config_extractor.extract(runtime.job_properties)
       -> service_factory.build(runtime, worker_config)
       -> service.serve()  [infinite loop]

Queue-driven worker iteration (parse/chunk/embed/index):
  pop_message() [acks message immediately]
  -> start_run()
  -> add_input()/add_output()
  -> process + write
  -> complete_run() OR fail_run()
  -> produce next-queue message (if stage outputs downstream work)

Polling worker iteration (scan/manifest/metrics):
  list_keys()/iterate
  -> start_run() [per item for scan/manifest; per cycle for metrics]
  -> process/write
  -> complete_run()/fail_run()/abort_run()
  -> sleep(poll_interval_seconds) [scan/manifest/metrics only]
```

---

## 3) Infrastructure Boundaries

### 3.1 Queue Integration Boundary

Queue boundary is `StageQueue` in pipeline-common gateway layer.
- Startup injects queue config from DataHub job properties.
- Worker services call only gateway methods (`pop_message`, `push_produce_message`, `push_dlq_message`).

```text
Evidence
- libs/pipeline-common/src/pipeline_common/gateways/queue/queue.py
- libs/pipeline-common/src/pipeline_common/gateways/factories/queue_gateway_factory.py
- libs/pipeline-common/src/pipeline_common/startup/runtime_factory.py
```

### 3.2 Storage Integration Boundary

Storage boundary is `ObjectStorageGateway` + `S3Client` adapter.
- Workers consume storage through gateway methods (`read_object`, `write_object`, `list_keys`, `copy`, `delete`).

```text
Evidence
- libs/pipeline-common/src/pipeline_common/gateways/object_storage/object_storage.py
- libs/pipeline-common/src/pipeline_common/gateways/factories/object_storage_gateway_factory.py
```

### 3.3 Processing Engine Abstraction Boundary

There is no shared processing-engine abstraction in `pipeline_common`.
- Domain logic directly executes local Python functions/libraries.
- Examples:
  - parse: `trafilatura` via `HtmlParser`
  - chunk: pure Python chunking function
  - embed: deterministic pseudo-embedding via `hashlib`
  - index: HTTP calls to Weaviate adapter

```text
Evidence
- domains/worker_parse_document/src/parsing/html/html_parser.py
- domains/worker_chunk_text/src/chunking/domain/text_chunker.py
- domains/worker_embed_chunks/src/services/worker_embed_chunks_service.py
- domains/worker_index_weaviate/src/services/weaviate_gateway.py
```

### 3.4 Coupling to Current Processing Approach

Coupling is currently **service-internal and stage-specific**:
- Processing implementation is embedded directly in each worker service.
- No cross-worker engine facade for batch/partition execution.
- Runtime startup has no concept of execution engine lifecycle.

---

## 4) Data Processing Engine Assessment

### 4.1 How Processing Is Implemented Today

- `worker_scan`: storage copy + queue produce.
- `worker_parse_document`: parse single document payload.
- `worker_chunk_text`: chunk one processed text payload.
- `worker_embed_chunks`: deterministic vector generation per chunk.
- `worker_index_weaviate`: upsert vectors to Weaviate.
- `worker_manifest` / `worker_metrics`: periodic storage scans.

All processing is synchronous Python in-process.

### 4.2 Where Engine Is Instantiated

There is no explicit “engine” object instantiated in startup or services.
- No SparkSession / distributed execution context exists.
- Processing code paths instantiate only local helpers/adapters.

### 4.3 Tight Coupling Assessment

Coupling is moderate-high at worker service layer because algorithms and IO orchestration are interleaved.
- Example: per-item lineage + storage + queue + compute all in one method.
- This will increase migration effort if Spark requires separate job planning/execution layers.

### 4.4 Existing Abstraction Layer?

Existing abstractions are for startup and infrastructure only.
- Present: startup contracts, queue/storage/lineage gateways.
- Missing: processing runtime abstraction (local vs Spark engine).

---

## 5) Architectural Alignment Analysis (vs docs/ARCHITECTURE.md)

### 5.1 Areas Aligned

1. Composition roots are explicit and thin.
2. Shared startup path is standardized (`RuntimeContextFactory` + `WorkerRuntimeLauncher`).
3. Gateway adapters isolate core external dependencies (queue/storage/lineage).
4. Dependency direction is correct (domains depend on libs; libs do not depend on domains).

```text
Evidence
- docs/ARCHITECTURE.md
- domains/worker_*/src/app.py
- libs/pipeline-common/src/pipeline_common/startup/*
- libs/pipeline-common/src/pipeline_common/gateways/*
```

### 5.2 Observed Divergences / Violations

1. Documented worker golden path says workers process queue payloads, but `worker_manifest` and `worker_metrics` are storage-polling loops, and `worker_scan` is storage-scan driven rather than queue-consume.
2. All workers request queue settings in startup, including workers that do not consume queue messages (`worker_manifest`, `worker_metrics`).
3. `poll_interval_seconds` is extracted for queue-driven workers (parse/chunk/embed/index) but not used in their loops.
4. Startup has side effects during object construction (DataHub metadata fetch, AMQP connect, bucket bootstrap, Weaviate schema check), which the architecture doc flags as known debt.
5. Queue ack happens before processing success, so acknowledgement semantics are not coupled to successful processing completion.

```text
Evidence
- domains/worker_manifest/src/services/worker_manifest_service.py
- domains/worker_metrics/src/services/worker_metrics_service.py
- domains/worker_scan/src/services/scan_cycle_processor.py
- domains/worker_*/src/app.py
- domains/worker_parse_document/src/services/worker_parse_document_service.py
- domains/worker_chunk_text/src/services/worker_chunk_text_service.py
- domains/worker_embed_chunks/src/services/worker_embed_chunks_service.py
- domains/worker_index_weaviate/src/services/worker_index_weaviate_service.py
- libs/pipeline-common/src/pipeline_common/gateways/queue/queue.py
```

### 5.3 Missing Abstractions Blocking Spark Migration

1. No execution-engine port/facade in shared runtime.
2. No worker lifecycle hook for initializing and reusing a long-lived engine session.
3. No standardized “processing unit” interface decoupled from queue/storage orchestration.
4. No distributed data contract (partitioning, schema, serialization) across stage processors.

### 5.4 Technical Debt Impacting Migration

1. Interleaved IO + compute in service methods will make incremental Spark adoption harder.
2. At-most-once queue ack behavior increases risk during larger/slower distributed compute.
3. Side effects in startup constructors complicate deterministic bootstrap and testability.

---

## 6) Spark Integration Strategy

### 6.1 Minimal Changes to Introduce Spark Cluster Usage

Goal: introduce Spark with smallest boundary expansion while preserving current worker topology.

Strategy:
1. Add a processing-engine abstraction in `libs/pipeline-common` (e.g., `ProcessingEngineGateway`).
2. Add Spark implementation (`SparkProcessingEngineGateway`) that owns SparkSession lifecycle.
3. Inject engine via `WorkerRuntimeContext` and worker service factories.
4. Migrate compute-heavy stages first (`worker_chunk_text`, then `worker_embed_chunks`) to engine-backed processors.
5. Keep queue/storage/lineage gateways unchanged initially.

### 6.2 Where SparkSession Should Be Instantiated

Instantiate once per worker process during startup context assembly, not per message:
- Preferred location: extend `RuntimeContextFactory` to build engine gateway.
- Store engine in `WorkerRuntimeContext` and reuse inside `service.serve()` loop.

Reason:
- Matches current startup pattern.
- Avoids repeated session boot overhead.
- Preserves composition-root simplicity.

### 6.3 Is a Processing Abstraction Needed?

Yes. Required to avoid hard-binding services directly to Spark APIs and to preserve ability to run local mode for fallback/tests.

Recommended minimal port:
- `run_chunking(payload) -> list[chunk_record]`
- `run_embedding(payload, dimension) -> embedding_record`
- Optional future: `run_batch(records)` for partitioned workloads

### 6.4 Does Current Worker Lifecycle Support Spark Reuse?

Yes, partially:
- Infinite loops and startup wiring support long-lived runtime dependencies.
- Missing piece: explicit lifecycle teardown hooks for engine shutdown.

Recommendation:
- Add optional `close()` in runtime launcher/service contracts (or wrapper) for graceful Spark stop.

### 6.5 Required Docker Changes

For Spark-enabled workers:
1. Add Java runtime (required by Spark).
2. Add `pyspark` dependency in worker images.
3. Add Spark env vars (`SPARK_MASTER_URL`, app name, executor/driver configs).
4. Decide mode:
   - Local mode first for minimal operational change.
   - Cluster mode next with external Spark master/workers.
5. Use `apache/spark:3.5.1` as the Spark runtime image baseline.

No new service is introduced in this planning step, but future cluster mode will require Spark infra domain compose definitions.

### 6.6 Required Dependency Changes

- Worker domain `pyproject.toml` for Spark-target stages: add `pyspark`.
- Potentially add a shared engine module in `libs/pipeline-common` and include in `pipeline-common` dependencies.
- Keep existing stage dependencies unchanged for first migration increment.

### 6.7 All worker services must accept SparkSession parameter

Direction:
- All worker service classes must take `spark_session` as a constructor parameter so review and migration focus is centralized in service and service-factory wiring.
- This applies to:
  - `WorkerScanService` (`domains/worker_scan/src/services/worker_scan_service.py`)
  - `WorkerParseDocumentService` (`domains/worker_parse_document/src/services/worker_parse_document_service.py`)
  - `WorkerChunkTextService` (`domains/worker_chunk_text/src/services/worker_chunk_text_service.py`)
  - `WorkerEmbedChunksService` (`domains/worker_embed_chunks/src/services/worker_embed_chunks_service.py`)
  - `WorkerIndexWeaviateService` (`domains/worker_index_weaviate/src/services/worker_index_weaviate_service.py`)
  - `WorkerManifestService` (`domains/worker_manifest/src/services/worker_manifest_service.py`)
  - `WorkerMetricsService` (`domains/worker_metrics/src/services/worker_metrics_service.py`)

Rules:
- SparkSession must be created once at startup and injected through each worker service factory.
- Non-compute workers may keep `spark_session` unused initially, but the parameter must exist for signature consistency.
- SparkSession must not be created/stopped per message; lifecycle is process-level.

---

## 7) Refactor Steps (Ordered Tasks)

### Step 1: Introduce Processing Engine Port in Shared Runtime
- Files to modify:
  - `libs/pipeline-common/src/pipeline_common/startup/runtime_context.py`
  - `libs/pipeline-common/src/pipeline_common/startup/contracts.py`
  - New module: `libs/pipeline-common/src/pipeline_common/gateways/processing_engine/*`
- Why:
  - Establish stable abstraction before Spark-specific implementation.
- Expected impact:
  - No runtime behavior change if default/local implementation is no-op/local Python.
- Risk:
  - Low

### Step 2: Add Spark Engine Adapter and Settings
- Files to modify:
  - `libs/pipeline-common/src/pipeline_common/settings/provider.py`
  - New module: `libs/pipeline-common/src/pipeline_common/gateways/processing_engine/spark.py`
  - `libs/pipeline-common/src/pipeline_common/startup/runtime_factory.py`
- Why:
  - Build SparkSession once and inject into runtime context.
- Expected impact:
  - Startup path gains optional engine initialization.
- Risk:
  - Medium

### Step 3: Wire Engine Through Worker Service Factories
- Files to modify:
  - `domains/worker_scan/src/startup/service_factory.py`
  - `domains/worker_parse_document/src/startup/service_factory.py`
  - `domains/worker_chunk_text/src/startup/service_factory.py`
  - `domains/worker_embed_chunks/src/startup/service_factory.py`
  - `domains/worker_index_weaviate/src/startup/service_factory.py`
  - `domains/worker_manifest/src/startup/service_factory.py`
  - `domains/worker_metrics/src/startup/service_factory.py`
- Why:
  - Enforce a uniform constructor contract where every worker service receives `spark_session`.
- Expected impact:
  - All service constructor signatures and factory wiring change; behavior remains the same where Spark is not yet used.
- Risk:
  - Medium

### Step 4: Extract Compute Logic from Services to Engine-Aware Processors
- Files to modify:
  - `domains/worker_scan/src/services/worker_scan_service.py`
  - `domains/worker_parse_document/src/services/worker_parse_document_service.py`
  - `domains/worker_chunk_text/src/services/worker_chunk_text_service.py`
  - `domains/worker_embed_chunks/src/services/worker_embed_chunks_service.py`
  - `domains/worker_index_weaviate/src/services/worker_index_weaviate_service.py`
  - `domains/worker_manifest/src/services/worker_manifest_service.py`
  - `domains/worker_metrics/src/services/worker_metrics_service.py`
  - New processor modules under each worker domain (e.g., `services/processors/*`)
- Why:
  - Keep service classes as the primary review boundary and separate orchestration (queue/storage/lineage) from compute execution.
- Expected impact:
  - Cleaner test boundaries and consistent service-level integration points for Spark across all workers.
- Risk:
  - Medium

### Step 5: Implement Spark-Backed Chunking Path
- Files to modify:
  - `domains/worker_chunk_text/src/services/...`
  - New spark processor for chunking
- Why:
  - Chunking is first compute-heavy candidate and upstream for downstream stages.
- Expected impact:
  - Chunk generation runs via Spark pipeline in configured mode.
- Risk:
  - High

### Step 6: Implement Spark-Backed Embedding Path (or Spark-Orchestrated embedding call path)
- Files to modify:
  - `domains/worker_embed_chunks/src/services/...`
  - New spark processor for embedding transformation
- Why:
  - Complete migration of main transformation stages.
- Expected impact:
  - Embedding stage throughput/scaling model changes.
- Risk:
  - High

### Step 7: Add Engine Lifecycle and Graceful Shutdown Hooks
- Files to modify:
  - `libs/pipeline-common/src/pipeline_common/startup/launcher.py`
  - `libs/pipeline-common/src/pipeline_common/startup/contracts.py`
- Why:
  - Ensure Spark sessions/connections are explicitly closed on termination.
- Expected impact:
  - Better resource control; cleaner stop semantics.
- Risk:
  - Medium

### Step 8: Rationalize Queue Ack/Failure Semantics Before Production Spark Rollout
- Files to modify:
  - `libs/pipeline-common/src/pipeline_common/gateways/queue/queue.py`
  - Queue-using worker services for explicit ack success/failure flow
- Why:
  - Longer compute windows increase loss risk with early ack behavior.
- Expected impact:
  - More reliable processing guarantees.
- Risk:
  - High

### Step 9: Docker and Runtime Configuration Enablement
- Files to modify:
  - `domains/worker_chunk_text/Dockerfile`
  - `domains/worker_embed_chunks/Dockerfile`
  - `domains/worker_chunk_text/docker-compose.yml`
  - `domains/worker_embed_chunks/docker-compose.yml`
  - possibly shared env docs under `docs/` and worker READMEs
- Why:
  - Provide Java/Spark runtime and config wiring.
- Expected impact:
  - Larger images and additional runtime parameters.
- Risk:
  - Medium

### Step 10: Update Architecture Docs After Structural Changes
- Files to modify:
  - `docs/ARCHITECTURE.md`
  - `libs/pipeline-common/src/pipeline_common/startup/docs/ARCHITECTURE.md`
  - worker docs for changed domains
- Why:
  - Keep architecture contracts and implementation synchronized.
- Expected impact:
  - Documentation alignment.
- Risk:
  - Low

### Implementation Status (as of 2026-03-03)

Status labels:
- `Done`: Implemented in codebase.
- `Partial`: Started but not fully aligned with planned end-state.
- `Pending`: Not yet implemented.

1. Step 1 (Processing engine port in shared runtime): `Partial`
   - Spark session wiring exists, but no full processing-engine facade/port abstraction for stage compute paths.
2. Step 2 (Spark engine adapter and settings): `Done`
   - Spark settings, Spark session builder, and runtime startup integration are implemented.
3. Step 3 (Wire engine through worker service factories): `Done`
   - All worker service factories inject `runtime.spark_session`; all worker apps request `spark=True`.
4. Step 4 (Extract compute logic into processors): `Done`
   - Worker services now delegate core compute/flow logic to processor/component modules.
5. Step 5 (Spark-backed chunking path): `Done`
   - `worker_chunk_text` now executes chunk splitting through Spark when `spark_session` is available, with local fallback when Spark is disabled.
6. Step 6 (Spark-backed embedding path): `Done`
   - `worker_embed_chunks` now executes embedding-vector computation through Spark when `spark_session` is available, with local deterministic fallback when Spark is disabled.
7. Step 7 (Engine lifecycle + graceful shutdown): `Done`
   - Launcher finalization now stops Spark session via shared helper.
8. Step 8 (Queue ack/failure semantics): `Done`
   - Queue consume now returns explicit message receipts with worker-controlled `ack()` / `nack(requeue=...)` semantics.
   - Backward-compat eager-ack pop behavior was removed; queue consumers must now settle messages explicitly.
   - Queue-driven workers (`parse/chunk/embed/index`) now acknowledge only after successful handling, and requeue when failure-to-DLQ routing occurs.
   - Invalid queue payloads are no longer dropped; they are published to stage DLQ (`*.invalid_message`) and then acknowledged. If DLQ publish fails, messages are requeued.
9. Step 9 (Docker/runtime Spark enablement): `Done` (chunk/embed scope)
   - Spark base image, Spark env vars, and `pyspark` dependency are enabled for `worker_chunk_text` and `worker_embed_chunks`.
10. Step 10 (Architecture docs sync): `Pending`
   - Architecture docs have not yet been updated to reflect Spark runtime/engine boundary changes.

---

## 8) Risk and Impact Analysis

### 8.1 Operational Risks

1. Spark initialization failures can prevent worker startup.
2. Cluster connectivity issues can stall queue processing.
3. Increased memory/CPU requirements can destabilize current container sizing.

### 8.2 Runtime Behavior Changes

1. Processing latency profile changes (batch/distributed overhead vs current single-item local execution).
2. Failure surfaces expand (Spark driver/executor errors, serialization issues).
3. Ordering/throughput characteristics may shift under partitioned execution.

### 8.3 Resource Impact

1. Higher baseline memory/CPU per Spark-enabled worker.
2. Additional Java runtime overhead in containers.
3. Potential storage and network amplification from batch shuffles and larger intermediate payloads.

### 8.4 Backward Compatibility Concerns

1. Message contracts must remain unchanged unless all downstream stages are coordinated.
2. Output object schemas/paths must remain stable to avoid breaking manifest/metrics/index behavior.
3. DataHub lineage semantics (`start_run/add_input/add_output/complete/fail`) must remain preserved.

### 8.5 Existing Risks to Address Pre-Migration

1. Early queue ack can lose work on mid-processing failures.
2. Inconsistent failure handling across workers (`abort_run` vs `fail_run`, partial exception coverage).
3. Queue dependency is loaded for polling workers that do not consume queue messages.

---

## 9) Final State Architecture Diagram (Text)

```text
[domains/worker_*/src/app.py]  (Composition Root)
  -> SettingsProvider + SettingsRequest(capabilities)
  -> RuntimeContextFactory
      -> LineageRuntimeGateway (DataHub)
      -> ObjectStorageGateway (S3)
      -> StageQueueGateway (AMQP)
      -> ProcessingEngineGateway (Spark or Local)
      -> Parsed job_properties
  -> WorkerRuntimeLauncher
      -> WorkerConfigExtractor
      -> WorkerServiceFactory
      -> WorkerService.serve()

Worker service responsibilities (post-migration):
  - Orchestrate per-unit flow (queue/storage/lineage/error policy)
  - Delegate compute to ProcessingEngineGateway-backed processors

Processing responsibilities (post-migration):
  - Spark adapter executes chunk/embed transforms with reusable SparkSession
  - Optional local adapter retained for tests/fallback

Boundary alignment with docs/ARCHITECTURE.md principles:
  - Composition roots remain in domains
  - Shared startup remains in libs/pipeline-common
  - Infra adapters remain isolated in gateways
  - New engine adapter added as another gateway boundary
```

---

## Appendix: Concrete Evidence Map

```text
Core architecture
- docs/ARCHITECTURE.md
- libs/pipeline-common/src/pipeline_common/startup/docs/ARCHITECTURE.md

Startup and wiring
- libs/pipeline-common/src/pipeline_common/startup/contracts.py
- libs/pipeline-common/src/pipeline_common/startup/runtime_context.py
- libs/pipeline-common/src/pipeline_common/startup/runtime_factory.py
- libs/pipeline-common/src/pipeline_common/startup/launcher.py

Settings and factories
- libs/pipeline-common/src/pipeline_common/settings/provider.py
- libs/pipeline-common/src/pipeline_common/gateways/factories/lineage_gateway_factory.py
- libs/pipeline-common/src/pipeline_common/gateways/factories/object_storage_gateway_factory.py
- libs/pipeline-common/src/pipeline_common/gateways/factories/queue_gateway_factory.py

Gateway implementations
- libs/pipeline-common/src/pipeline_common/gateways/lineage/lineage.py
- libs/pipeline-common/src/pipeline_common/gateways/object_storage/object_storage.py
- libs/pipeline-common/src/pipeline_common/gateways/queue/queue.py

Worker domains
- domains/worker_*/src/app.py
- domains/worker_*/src/startup/config_extractor.py
- domains/worker_*/src/startup/service_factory.py
- domains/worker_*/src/services/*.py

Operational launch
- stack.sh
- tooling/ops/cmd/up.sh
- tooling/ops/lib/compose.sh
- tooling/ops/lib/core.sh
- domains/worker_*/docker-compose.yml
- domains/worker_*/Dockerfile

Governance runtime config source
- domains/gov_governance/definitions/600_jobs/600_governed-rag.yaml
- registry/datahub_job_key_registry.py
```
