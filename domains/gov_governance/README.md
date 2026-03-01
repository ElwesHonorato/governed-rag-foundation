# Governance IaC for DataHub

This directory defines static DataHub metadata as code: versioned, reviewable, repeatable, and idempotent.

## Layout

- `definitions/`: domains, groups, tags, glossary terms, datasets, and pipelines/jobs
- `src/`: apply entrypoints
- `ci/github/workflows/`: example CI workflows for check/apply

## Usage

Run from repo root.

Set DataHub environment variables:

```bash
export DATAHUB_GMS_SERVER="http://localhost:8081"
export DATAHUB_ENV="DEV"
export DATAHUB_TOKEN="..."
```

```bash
PYTHONPATH=libs/pipeline-common/src .venv/bin/python domains/gov_governance/src/apply.py
```

Use PROD target:

```bash
export DATAHUB_GMS_SERVER="https://datahub.company.com"
export DATAHUB_ENV="PROD"
export DATAHUB_TOKEN="..."
PYTHONPATH=libs/pipeline-common/src .venv/bin/python domains/gov_governance/src/apply.py
```

## Workflow

1. Edit YAML under `definitions/`.
2. Apply from trusted branch using `apply.py`.

## Idempotency

`apply.py` uses upserts and can be rerun safely. Existing entities are updated to match definitions.
