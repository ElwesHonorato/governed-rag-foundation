# Governance IaC for DataHub

This directory defines static DataHub metadata as code: versioned, reviewable, repeatable, and idempotent.

## Layout

- `configs/`: environment-specific DataHub connection and environment label
- `definitions/`: domains, groups, tags, glossary terms, datasets, and pipelines/jobs
- `scripts/`: validate, plan, bootstrap, and apply entrypoints
- `ci/github/workflows/`: example CI workflows for check/apply

## Usage

Run from repo root.

Set environment once (default is `dev` if not set):

```bash
export ENV=dev
```

```bash
.venv/bin/python governance/scripts/validate.py
.venv/bin/python governance/scripts/plan.py
.venv/bin/python governance/scripts/bootstrap.py
.venv/bin/python governance/scripts/apply.py
```

Use prod config:

```bash
export DATAHUB_TOKEN_PROD="..."
export ENV=prod
.venv/bin/python governance/scripts/apply.py
```

## Workflow

1. Edit YAML under `definitions/`.
2. Run `validate.py` locally.
3. Review `plan.py` output in PR.
4. Apply from trusted branch using `apply.py`.

## Idempotency

`apply.py` uses upserts and can be rerun safely. Existing entities are updated to match definitions.
