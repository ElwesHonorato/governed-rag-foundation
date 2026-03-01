# Error Handling

## Intent
Keep workers resilient in long-running loops while preserving traceability of failures.

## When To Use
- Queue-driven worker loops.
- Object processing pipelines that emit lineage or downstream queue events.

## How To Apply
1. Catch exceptions at loop boundaries to avoid process-wide crash loops.
2. Push failed messages to DLQ when queue contract supports it.
3. Mark lineage run failure/abort when processing fails.
4. Log enough context (keys/doc IDs/stage) to diagnose quickly.

## Example
- Worker service loop catches exceptions, logs, and continues.
- Processor methods fail one unit-of-work and continue polling for next message.

## Anti-Patterns
- Swallowing exceptions without logging or lineage status updates.
- Crashing the whole worker on one malformed message.
- Retrying indefinitely without DLQ or failure visibility.

## Notes
- Retry policies are currently worker-specific; no global retry framework is defined yet. TODO: standardize retry/backoff policy.
