#!/usr/bin/env bash
set -euo pipefail

find . -name pyproject.toml -not -path '*/.venv/*' -print0 \
| xargs -0 -n1 dirname \
| sort -u \
| while IFS= read -r d; do
  printf '\n============================================================\n'
  printf 'PROJECT: %s\n' "$d"
  printf 'ACTION : POETRY_VIRTUALENVS_CREATE=false poetry lock -vvv\n'
  printf '============================================================\n\n'
  (cd "$d" && POETRY_VIRTUALENVS_CREATE=false poetry lock -vvv) || {
    printf '\n[FAILED] %s\n' "$d"
    exit 1
  }
  printf '\n[OK] %s\n' "$d"
  printf 'LOCK   : %s/poetry.lock\n' "$d"
done
