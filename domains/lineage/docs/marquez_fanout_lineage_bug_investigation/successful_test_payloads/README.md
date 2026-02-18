# Successful OpenLineage Payload Test (Marquez)

This folder contains the exact JSON payloads that were tested successfully against Marquez.

## Preconditions

1. Lineage stack is running (`marquez` + `postgres`):
   ```bash
   ./stack.sh ps lineage
   ```
2. Marquez API is healthy on the Docker network.

## Replicate The Test

Run from repo root:

```bash
cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/successful_test_payloads/01_worker_scan_start.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"
cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/successful_test_payloads/02_worker_scan_complete.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"

cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/successful_test_payloads/03_worker_parse_document_start.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"
cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/successful_test_payloads/04_worker_parse_document_complete.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"

cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/successful_test_payloads/05_worker_chunk_text_start.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"
cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/successful_test_payloads/06_worker_chunk_text_complete.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"

cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/successful_test_payloads/07_worker_embed_chunks_start.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"
cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/successful_test_payloads/08_worker_embed_chunks_complete.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"

cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/successful_test_payloads/09_worker_index_weaviate_start.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"
cat domains/lineage/docs/marquez_fanout_lineage_bug_investigation/successful_test_payloads/10_worker_index_weaviate_complete.openlineage.json | docker exec -i rag-lineage-marquez-1 sh -lc "cat >/tmp/ol_event.json && curl -sS -i -X POST http://marquez:5000/api/v1/lineage -H 'Content-Type: application/json' --data @/tmp/ol_event.json"
```

Expected result for each POST:

- `HTTP/1.1 201 Created`

## Verify In UI

1. Open Marquez UI: `http://localhost:3000`
2. Check namespace `governed-rag` for jobs.
3. Check namespace `rag-data` for datasets.
4. Open job lineage graph to confirm stage chain:
   - `worker_scan -> worker_parse_document -> worker_chunk_text -> worker_embed_chunks -> worker_index_weaviate`
