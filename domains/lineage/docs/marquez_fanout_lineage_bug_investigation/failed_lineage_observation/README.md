# Failed Lineage Observation Test (Marquez)

This folder contains the exact JSON payloads used to reproduce a lineage inconsistency in Marquez.

Related upstream issue (opened after this investigation):
- https://github.com/MarquezProject/marquez/issues/3093

## Preconditions

1. Lineage stack is running (`marquez` + `postgres`):
   ```bash
   ./stack.sh ps lineage
   ```
2. Marquez API is healthy on the Docker network.
3. Start from a clean Marquez DB (purge before replay).

## Replicate The Test

Run from repo root.

### 1) Post first stages (producer chain)

```bash
cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/failed_lineage_observation/01_02_scan/01_02_worker_scan_start.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"
cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/failed_lineage_observation/01_02_scan/01_02_worker_scan_complete.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"

cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/failed_lineage_observation/02_03_parse_document/02_03_worker_parse_document_start.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"
cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/failed_lineage_observation/02_03_parse_document/02_03_worker_parse_document_complete.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"

cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/failed_lineage_observation/03_04_chunk_text/03_04_worker_chunk_text_start_chunk_1.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"
cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/failed_lineage_observation/03_04_chunk_text/03_04_worker_chunk_text_complete_chunk_1.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"

cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/failed_lineage_observation/03_04_chunk_text/03_04_worker_chunk_text_start_chunk_2.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"
cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/failed_lineage_observation/03_04_chunk_text/03_04_worker_chunk_text_complete_chunk_2.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"
```

### 2) Post embed for chunk 1, observe UI

```bash
cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/failed_lineage_observation/04_05_embed_chunks/04_05_worker_embed_chunks_start_chunk_1.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"
cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/failed_lineage_observation/04_05_embed_chunks/04_05_worker_embed_chunks_complete_chunk_1.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"
```

### 3) Post embed for chunk 2, observe UI again

```bash
cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/failed_lineage_observation/04_05_embed_chunks/04_05_worker_embed_chunks_start_chunk_2.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"
cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/failed_lineage_observation/04_05_embed_chunks/04_05_worker_embed_chunks_complete_chunk_2.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"
```

Expected result for each POST:
- `HTTP/1.1 201 Created`

## Verify In UI

1. Open Marquez UI: `http://localhost:3000`
2. Open lineage for job `worker_embed_chunks`.
3. Observation:
   - after chunk 1: lineage is connected for chunk 1.
   - after chunk 2: chunk 2 lineage is connected, but chunk 1 can appear disconnected.

## Additional Evidence

For backend evidence and API outputs, see:
- `domains/lineage/docs/marquez_fanout_lineage_bug_investigation/failed_lineage_observation/marquez_issue_repro_embed_isolated.md`
