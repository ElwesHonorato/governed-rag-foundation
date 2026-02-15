# Lineage Scripts

Small Python tooling for querying Marquez lineage data.

## Entrypoint

- `scripts/lineage/lineage.py`

## Make Targets

```bash
make lineage-help
make lineage-namespaces
make lineage-jobs
make lineage-jobs ns=governed-rag
make lineage-datasets
make lineage-datasets ns=s3://rag-data
make lineage-search q=<text>
make lineage-chunk q=<chunk_id>
```

## Commands

```bash
python3 scripts/lineage/lineage.py namespaces
python3 scripts/lineage/lineage.py jobs [namespace]
python3 scripts/lineage/lineage.py datasets [namespace]
python3 scripts/lineage/lineage.py search <text>
python3 scripts/lineage/lineage.py chunk <chunk_id>
```

## Environment

- `MARQUEZ_API_URL` expected (example: `http://localhost:5000/api/v1`)
- `LINEAGE_JOB_NAMESPACE` expected (example: `governed-rag`)
- `LINEAGE_DATASET_NAMESPACE` expected (example: `s3://rag-data`)
- `NO_COLOR=1` disables ANSI colors in output.

## Module Layout

- `_config.py`
  - Required env loading and typed runtime config.
- `_output.py`
  - ANSI-aware output helpers and JSON rendering.
- `_commands.py`
  - Command handlers (`namespaces`, `jobs`, `datasets`, `search`, `chunk`).
- `lineage.py`
  - CLI argument parsing and command dispatch.

Shared API client:
- `libs/pipeline-common/src/pipeline_common/lineage/api.py`

## Notes

- This script is Marquez-only (no Weaviate queries).
- `chunk` command is intentionally minimal: context + Marquez search output.
