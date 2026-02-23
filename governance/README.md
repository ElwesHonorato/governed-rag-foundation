# Governance IaC for DataHub

This directory defines static DataHub metadata as code: versioned, reviewable, repeatable, and idempotent.

## Layout

- `configs/`: environment-specific DataHub connection settings
- `definitions/`: domains, groups, tags, glossary terms, datasets, and pipelines/jobs
- `src/`: apply entrypoints
- `ci/github/workflows/`: example CI workflows for check/apply

## Usage

Run from repo root.

Set environment once (default is `dev` if not set):

```bash
export ENV=dev
```

```bash
PYTHONPATH=libs/pipeline-common/src .venv/bin/python governance/src/apply.py
```

Use prod config:

```bash
export DATAHUB_TOKEN_PROD="..."
export ENV=prod
PYTHONPATH=libs/pipeline-common/src .venv/bin/python governance/src/apply.py
```

## Workflow

1. Edit YAML under `definitions/`.
2. Apply from trusted branch using `apply.py`.

## Idempotency

`apply.py` uses upserts and can be rerun safely. Existing entities are updated to match definitions.
