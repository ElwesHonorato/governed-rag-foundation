# Backlog

## Queue DLQ Routing Follow-Up (worker_chunk_text)

1. Finalize DLQ routing and failure-settlement strategy for `worker_chunk_text`:
   1. Verify RabbitMQ dead-letter policy/arguments for `q.chunk_text` so `nack(requeue=False)` routes to `q.chunk_text.dlq`.
   2. Decide on one failure strategy to avoid duplicates:
      1. Broker DLQ only (`nack(requeue=False)`), or
      2. Explicit `push_dlq(...)` + `ack()`.
   3. If using broker DLQ, remove/adjust manual `push_dlq(...)` failure publish path.
   4. If using explicit DLQ publish, ensure fallback behavior is clearly defined when DLQ publish fails.
   5. Add/update tests for failure settlement behavior and expected DLQ message shape.
   6. Update `domains/worker_chunk_text/docs/ARCHITECTURE.md` queue settlement policy to match final implementation.
2. Standardize run ID generation across workers using `pipeline_common.helpers.run_ids.build_source_run_id(...)` and develop strong uniqueness via central coordination/store with conflict handling.
