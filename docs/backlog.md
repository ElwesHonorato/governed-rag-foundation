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
