#!/usr/bin/env bash
set -euo pipefail

compose_file_for_domain() {
  local domain="$1"
  echo "$REPO_ROOT/domains/$domain/docker-compose.yml"
}

compose_dev_file_for_domain() {
  local domain="$1"
  echo "$REPO_ROOT/domains/$domain/docker-compose.dev.yml"
}

compose_files_for_domain() {
  local domain="$1"
  local base_file
  local dev_file

  base_file="$(compose_file_for_domain "$domain")"
  printf '%s\n' "$base_file"

  if [[ "$domain" == worker_* ]]; then
    dev_file="$(compose_dev_file_for_domain "$domain")"
    if [[ -f "$dev_file" ]]; then
      printf '%s\n' "$dev_file"
    fi
  fi
}

compose_project_for_domain() {
  local domain="$1"
  echo "rag-$domain"
}

compose_domain() {
  local domain="$1"
  local file
  local compose_files=()
  shift

  while IFS= read -r file; do
    compose_files+=(-f "$file")
  done < <(compose_files_for_domain "$domain")

  docker compose \
    --project-directory "$REPO_ROOT" \
    --project-name "$(compose_project_for_domain "$domain")" \
    "${compose_files[@]}" \
    "$@"
}
