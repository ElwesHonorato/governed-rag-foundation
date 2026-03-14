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
