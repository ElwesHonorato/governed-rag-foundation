# Backlog

## Queue DLQ Routing Follow-Up (worker_chunk_text)

1. Finalize DLQ routing and failure-settlement strategy for `worker_chunk_text`:
   a. Verify RabbitMQ dead-letter policy/arguments for `q.chunk_text` so `nack(requeue=False)` routes to `q.chunk_text.dlq`.
   b. Decide on one failure strategy to avoid duplicates: broker DLQ only (`nack(requeue=False)`) or explicit `push_dlq(...)` + `ack()`.
   c. If using broker DLQ, remove or adjust manual `push_dlq(...)` failure publish path.
   d. If using explicit DLQ publish, define fallback behavior when DLQ publish fails.
   e. Add or update tests for failure settlement behavior and expected DLQ message shape.
   f. Update `domains/worker_chunk_text/docs/ARCHITECTURE.md` queue settlement policy to match final implementation.
2. Standardize run ID generation across workers using `pipeline_common.helpers.run_ids.build_source_run_id(...)` and enforce strong uniqueness.
   a. Define central coordination or storage strategy for run ID uniqueness.
   b. Define conflict detection and conflict handling behavior.
   c. Update worker implementations to use the standardized strategy.

3. Define minimal chunk metadata while keeping a single shared cross-stage payload contract (`StageArtifact`).
   a. Evaluate `StageArtifactMetadata` usage for chunk artifacts and identify removable repeated fields.
   b. Decide what shared context should move to manifest-level storage versus remain in per-chunk payloads.
   c. Propose a contract shape that avoids metadata redundancy while preserving traceability.
   d. Keep contract semantics explicit (no ambiguous empty placeholders unless formally defined).
   e. Ensure downstream stages can resolve required context deterministically.
   f. Document the final pattern and required code migrations across impacted workers.

4. Remove hardcoded `s3a://` URI construction to decouple worker code from MinIO/S3A assumptions.
   a. Inventory all places building object URIs with literal `s3a://` (workers, processors, shared libs).
   b. Introduce a storage URI strategy (or helper) driven by runtime/storage config instead of hardcoded scheme.
   c. Keep object-storage gateway contracts explicit about when callers pass full URI vs bucket/key.
   d. Update worker message contracts where needed to avoid ambiguous URI/key handling.
   e. Add tests covering URI parsing/building behavior for configured schemes.
   f. Update architecture/pattern docs with the final storage URI policy and migration notes.

5. Replace scan-stage payload reads with metadata-based source checksums.
   a. Extend the object-storage gateway with a metadata/head operation that can return checksum fields without downloading the object body.
   b. Define the canonical checksum contract for workers: prefer storage-provided SHA-256 (or equivalent explicit checksum metadata), and reject ambiguous substitutes such as multipart `ETag`.
   c. Update the ingest/upload path to persist the canonical source checksum in object metadata when the storage backend does not provide it automatically.
   d. Refactor `worker_scan` to use metadata-only checksum lookup so scan remains a pure move operation and does not pull full source payloads into worker memory.
   e. Add tests covering checksum lookup success, missing checksum metadata, and the fail-fast behavior for unsupported objects.
   f. Document the storage checksum policy and the temporary current-state exception: until this lands, `worker_scan` keeps the existing read-and-hash implementation.

6. Add explicit LLM model selection instead of picking the first available model.
   a. Define where the selected model lives in runtime configuration and how callers provide or inherit it.
   b. Preserve `LLMGateway` as the boundary and avoid introducing wrapper contracts just to carry model state.
   c. Update agent execution and grounded-response paths to use the explicit model selection instead of `list_models()[0]`.
   d. Decide expected behavior when the configured model is missing, duplicated across providers, or the gateway returns no models.
   e. Add tests for configured-model success, no-models failure, and invalid-model failure.
   f. Update architecture/startup docs to describe the final model-selection flow and remove the temporary first-model fallback note.

7. Evaluate a shared WSGI HTTP mini-framework after standardizing the low-level HTTP primitives.
   a. Inventory what is still duplicated across API domains after sharing `WsgiRequestNormalizer`, `NormalizedRequest`, `JsonResponse`, and WSGI types.
   b. Decide whether a shared application boundary should exist or whether per-domain application classes should remain local.
   c. Define a single error-mapping policy for route misses, invalid JSON, validation errors, and uncaught exceptions.
   d. Decide whether health endpoints should use a shared payload contract or remain domain-specific.
   e. Prove the abstraction against at least the current `agent_api` and `app_elasticsearch` shapes before introducing framework-style base classes.
   f. Document guardrails so shared HTTP infrastructure does not absorb domain routing, handler logic, or service orchestration.

8. Add a query adapter between user intent and Elasticsearch lexical search.
   a. Define the contract boundary between user-facing retrieval requests and the internal Elasticsearch lexical query shape.
   b. Decide whether the adapter should remain a simple prompt-to-lexical translator or also support structured retrieval inputs.
   c. Keep Elasticsearch query construction out of the HTTP handler so request intent translation and search-policy behavior stay separate.
   d. Define fail-fast behavior for unsupported request shapes instead of silently dumping arbitrary prompts into lexical search.
   e. Add tests covering direct keyword queries, natural-language prompts, and invalid request forms.
   f. Document the boundary so future hybrid/vector retrieval work can extend the adapter without coupling API payloads to raw Elasticsearch DSL.
