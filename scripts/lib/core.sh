#!/usr/bin/env bash
set -euo pipefail

readonly STACK_NETWORK="rag-local"
readonly REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly LOCALDATA_DIR="$REPO_ROOT/localdata"
readonly DOMAINS=(storage vector cache lineage llm apps)

ui_use_color() {
  [[ -t 1 ]] && [[ -z "${NO_COLOR:-}" ]]
}

ui_print() {
  local level="$1"
  local message="$2"
  local label color="" reset=""

  case "$level" in
    title)
      label="title"
      color="1;36"
      ;;
    info)
      label="info"
      color="36"
      ;;
    action)
      label="step"
      color="34"
      ;;
    ok)
      label="ok"
      color="32"
      ;;
    warn)
      label="warn"
      color="33"
      ;;
    error)
      label="error"
      color="31"
      ;;
    *)
      label="$level"
      color="35"
      ;;
  esac

  if ui_use_color; then
    reset=$'\033[0m'
    printf '\033[%sm[%s]%s %s\n' "$color" "$label" "$reset" "$message"
  else
    printf '[%s] %s\n' "$label" "$message"
  fi
}

ui_rule() {
  if ui_use_color; then
    printf '\033[2m----------------------------------------\033[0m\n'
  else
    printf '%s\n' '----------------------------------------'
  fi
}

ui_space() {
  printf '\n'
}

ui_section() {
  local title="$1"
  ui_space
  ui_rule
  ui_print title "$title"
  ui_rule
}

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
    ui_print error "Invalid domain: $domain" >&2
    ui_print info "Valid domains: ${DOMAINS[*]}" >&2
    exit 1
  fi
}

require_domain_arg() {
  local domain="$1"
  if [[ -z "$domain" ]]; then
    ui_print error "A domain is required for this command." >&2
    ui_print info "Valid domains: ${DOMAINS[*]}" >&2
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
    "$LOCALDATA_DIR/postgres" \
    "$LOCALDATA_DIR/ollama"
}
