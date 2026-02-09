# Epic: HTML Vertical Slice (S3 -> Weaviate)

## Immediate Vertical Slice Plan (HTML: S3 -> Weaviate)
1. Define one canonical document contract.
- Input: `s3://rag-data/01_incoming/*.html`
- Output record fields (minimum): `doc_id`, `source_key`, `source_type`, `timestamp`, `security_clearance`, `title`, `text`.
2. Extend worker pipeline stages (HTML-only).
- `scan`: already exists.
- Add: `chunk_text` (`03_processed -> 04_chunks`), `embed_chunks` (`04_chunks -> 05_embeddings`), `index_weaviate` (`05_embeddings -> vector DB`).
- Persist intermediate artifacts in S3 so each stage is inspectable and retryable.
3. Parse HTML into processed artifacts.
- Extract cleaned visible text (strip scripts/styles/nav noise), title, and basic metadata.
4. Implement deterministic chunking.
- Use sentence/paragraph-aware chunking (not fixed raw character splits).
- Assign stable IDs: `chunk_id = hash(doc_id + chunk_index + chunk_text)`.
5. Implement embedding stage.
- Write vector + metadata JSON to `05_embeddings/`.
- Include metadata: `source_type`, `timestamp`, `security_clearance`, `doc_id`, `source_key`, `chunk_index`.
6. Implement Weaviate upsert + verification query.
- Upsert by `chunk_id` for idempotency.
- Add a minimal top-k verification query against a known test phrase.
7. Add a tiny ingestion status manifest.
- Track per-file stage status to prevent duplicate processing and make retries safe.
8. Add minimal observability.
- Add counters: files processed, chunks created, index upserts, failures.
9. Define acceptance criteria for this slice.
- Parsed artifact exists in `03_processed/`.
- Chunks exist in `04_chunks/`.
- Embeddings exist in `05_embeddings/`.
- Indexed chunks are queryable in Weaviate.

## Change Log
- 2026-02-09: Created epic ticket by extracting the HTML vertical-slice plan from `requirements/00-overview/requirements-coverage-roadmap.md`.
