# worker_scan domain

This domain is the pipeline starter. It watches incoming documents, moves valid files into the raw stage, and kicks off asynchronous processing.

## Deep Dive

### Stage responsibility
- Reads from the environment-scoped incoming prefix, for example `DEV/01_incoming/`.
- Moves accepted files to the environment-scoped raw prefix, for example `DEV/02_raw/`.
- Emits DataHub DPI events for scan runs.
- Enqueues parse jobs to the DataHub-configured `queue.produce` value for `worker_scan`.

### File selection behavior
- Processes all keys under the configured incoming prefix.
- Skips only the prefix placeholder key itself.

### Runtime dependencies
- `BROKER_URL` for queue publishing.
- `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` for object storage operations.
- `DATAHUB_GMS_SERVER`, `DATAHUB_ENV` (and optional `DATAHUB_TOKEN`) for DataHub runtime metadata.
- Processing config and queue routing are read from DataHub job `custom_properties` (source: `domains/gov_governance/definitions/600_jobs/600_governed-rag.yaml`).

### Operational notes
- Service container: `pipeline-worker-scan`.
- Queue names are resolved from DataHub job custom properties (`queue.produce`, `queue.dlq`) for `worker_scan`.
