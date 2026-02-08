#!/usr/bin/env bash
set -euo pipefail

readonly STACK_NETWORK="rag-local"
readonly REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly LOCALDATA_DIR="$REPO_ROOT/localdata"
readonly DOMAINS=(storage vector cache lineage apps)

is_valid_domain() {
  local domain="$1"
  local d
  for d in "${DOMAINS[@]}"; do
    if [[ "$d" == "$domain" ]]; then
      return 0
    fi
  done
  return 1
}

require_domain_if_provided() {
  local domain="$1"
  if [[ -n "$domain" ]] && ! is_valid_domain "$domain"; then
    echo "Invalid domain: $domain" >&2
    echo "Valid domains: ${DOMAINS[*]}" >&2
    exit 1
  fi
}

require_domain_arg() {
  local domain="$1"
  if [[ -z "$domain" ]]; then
    echo "A domain is required for this command." >&2
    echo "Valid domains: ${DOMAINS[*]}" >&2
    exit 1
  fi
  require_domain_if_provided "$domain"
}

selected_domains() {
  local domain="$1"
  require_domain_if_provided "$domain"
  if [[ -n "$domain" ]]; then
    echo "$domain"
  else
    printf '%s\n' "${DOMAINS[@]}"
  fi
}

ensure_localdata_dirs() {
  mkdir -p \
    "$LOCALDATA_DIR/minio" \
    "$LOCALDATA_DIR/weaviate" \
    "$LOCALDATA_DIR/redis" \
    "$LOCALDATA_DIR/postgres"
}
