# lineage domain

This domain runs DataHub quickstart for lineage storage, graph, and UI exploration.

## What runs here
- `datahub-gms`
- `datahub-frontend-react`
- `datahub-actions`
- `datahub-upgrade`
- `mysql`, `elasticsearch`, `neo4j`
- `broker`, `zookeeper`, `schema-registry`

Full compose definition: `domains/lineage/docker-compose.yml`.

## How to run
```bash
./stack.sh up lineage
./stack.sh ps lineage
./stack.sh logs lineage
./stack.sh down lineage
```

## Key endpoints
- DataHub UI: `http://localhost:${DATAHUB_MAPPED_FRONTEND_PORT}`
- DataHub GMS: `http://localhost:${DATAHUB_MAPPED_GMS_PORT}`
- OpenLineage ingest endpoint used by workers:
  `http://datahub-gms:8080/openapi/openlineage/api/v1/lineage`

## Worker lineage settings
- `DATAHUB_OPENLINEAGE_URL`
- `DATAHUB_TOKEN` (optional bearer token)
- Canonical namespaces in worker configs:
  - job namespace: `jobs-rag.local`
  - dataset namespace: `datasets-rag.local`

## Verification checks
```bash
make lineage-help
make lineage-jobs
make lineage-datasets
make lineage-search q=<text>
```
