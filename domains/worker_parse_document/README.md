# worker_parse_document domain

This domain turns raw documents into normalized processed payloads. Think of it as the parser and metadata normalizer for the pipeline.

## Deep Dive

### Stage responsibility
- Consumes `q.parse_document` messages containing `storage_key`.
- Reads raw objects from `02_raw/`.
- Parses content via parser registry (currently includes HTML parser).
- Writes processed JSON to `03_processed/{doc_id}.json`.
- Publishes downstream jobs to `q.chunk_text`.
- Sends parse failures to `q.parse_document.dlq` with error details.

### Payload characteristics
- Adds fields like `doc_id`, `source_key`, `timestamp`, `security_clearance`, and parser output.

### Runtime dependencies
- Queue: `BROKER_URL`.
- Storage: `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`.
- Parsing defaults: `SOURCE_TYPE`, `DEFAULT_SECURITY_CLEARANCE`.

### Operational notes
- Service container: `pipeline-worker-parse-document`.
- Queue contract stage: `parse_document`.
