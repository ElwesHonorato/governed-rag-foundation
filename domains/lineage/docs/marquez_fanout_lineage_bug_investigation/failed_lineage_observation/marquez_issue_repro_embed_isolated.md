# Potential Bug: Job lineage shows only one upstream edge for multi-run job with different IO sets

## Upstream Issue
- Root cause traced to an upstream defect in Marquez.
- Issue reported here:
  https://github.com/MarquezProject/marquez/issues/3093

## Context
I am testing OpenLineage ingestion with Marquez and observed a mismatch between:
- run history for a job, and
- job-level lineage edges shown for that same job.

This may be expected behavior, but if not, it looks like a lineage graph bug/regression for multi-run jobs.

## Environment
- Marquez container image: `marquezproject/marquez:latest` (running app jar: `marquez-api-0.51.1.jar`)
- Marquez API endpoint: `POST /api/v1/lineage`
- Namespace/job under test: `governed-rag / worker_embed_chunks`

## Repro Steps
1. Start from a clean Marquez DB.
2. Post `03_04_chunk_text` events.
3. Confirm `03_04_chunk_text` outputs exactly 2 datasets:
   - `04_chunks/...part1/...chunk.json`
   - `04_chunks/...part2/...chunk.json`
4. Post `04_05_embed_chunks` events with 2 independent runs:
   - Run A consumes `04_chunks/...part1/...chunk.json` and produces `05_embeddings/...part1/...embedding.json`
   - Run B consumes `04_chunks/...part2/...chunk.json` and produces `05_embeddings/...part2/...embedding.json`
5. Query both:
   - run history
   - job-level lineage graph

## Exact Evidence (from API)
### A) Linear producer/consumer expectation
- Producer stage (`03_04_chunk_text`) outputs 2 chunk files (`part1`, `part2`).
- Consumer stage (`04_05_embed_chunks`) processes each chunk independently in separate runs.
- Therefore, job-level lineage for `worker_embed_chunks` should show 2 upstream chunk edges.

### B) Run history confirms 2 independent consumer runs
Command:
```bash
docker exec rag-lineage-marquez-1 sh -lc \
  "curl -sS 'http://localhost:5000/api/v1/namespaces/governed-rag/jobs/worker_embed_chunks/runs?limit=20'"
```
Extracted results:
- `RUN_COUNT: 2`
- `RUN_INPUT_DATASETS:`
  - `04_chunks/a204e8b00fc95a95e854f4a0.part1/5d6fa2bd4c8f9fda94a1b948ae0c5a5db139bc6884acac22705d828b2d1a09bd.chunk.json`
  - `04_chunks/a204e8b00fc95a95e854f4a0.part2/40672b6cd77dc46285d180c7e0fe9f1c9e0725cfcbd6e12bfe415810b67d0bf8.chunk.json`

### C) Job lineage in-edge to embed shows only one upstream chunk
Command:
```bash
docker exec rag-lineage-marquez-1 sh -lc \
  "curl -sS 'http://localhost:5000/api/v1/lineage?nodeId=job%3Agoverned-rag%3Aworker_embed_chunks&depth=3'"
```
Extracted in-edge(s) to job:
- `"origin":"dataset:rag-data:04_chunks/...part2/...chunk.json","destination":"job:governed-rag:worker_embed_chunks"`

So: upstream produces 2 chunk datasets and consumer runs ingest both, but job-level lineage edge list reflects only one upstream chunk.

## Expected
At job-level lineage for `worker_embed_chunks`, I expect upstream connectivity to represent all relevant ingested runs (or a clearly documented mode if only latest run should be shown).

## Actual
Job-level lineage appears partial, reflecting only one upstream edge, while API run history confirms multiple valid upstream datasets across runs.

## Additional UI Observation (chronological)
- Right after processing `part1` only, UI lineage looked correct (connected chain for `part1`).
- After processing `part2`, the `part2` lineage looked correct, but `part1` started appearing as a disconnected node.
- This suggests previously visible upstream connectivity can be replaced/overwritten when a new run for the same job is ingested.

## Why this matters
In UI/graph investigation, this looks like disconnected/isolated lineage branches even though events were accepted (`201`) and run history is complete.

## Request
Please confirm whether this is:
1. intended "latest/current run only" job-lineage behavior, or
2. a bug/regression in lineage edge materialization for multi-run jobs.

If intended, is there a supported API/UI mode to view cumulative lineage across runs?
