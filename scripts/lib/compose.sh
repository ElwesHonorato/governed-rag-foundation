#!/usr/bin/env bash
set -euo pipefail

compose_file_for_domain() {
  local domain="$1"
  echo "$REPO_ROOT/domains/$domain/docker-compose.yml"
}

compose_project_for_domain() {
  local domain="$1"
  echo "rag-$domain"
}

compose_domain() {
  local domain="$1"
  shift
  docker compose \
    --project-directory "$REPO_ROOT" \
    --project-name "$(compose_project_for_domain "$domain")" \
    -f "$(compose_file_for_domain "$domain")" \
    "$@"
}
