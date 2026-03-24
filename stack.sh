#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$ROOT_DIR/tooling/ops/lib/core.sh"
source "$ROOT_DIR/tooling/ops/lib/network.sh"
source "$ROOT_DIR/tooling/ops/lib/compose.sh"
source "$ROOT_DIR/tooling/ops/cmd/up.sh"
source "$ROOT_DIR/tooling/ops/cmd/down.sh"
source "$ROOT_DIR/tooling/ops/cmd/logs.sh"
source "$ROOT_DIR/tooling/ops/cmd/ps.sh"
source "$ROOT_DIR/tooling/ops/cmd/wipe.sh"

usage() {
  cat <<'USAGE'
Usage:
  ./stack.sh up [domain] [--build]
  ./stack.sh down [domain]
  ./stack.sh wipe
  ./stack.sh logs <domain>
  ./stack.sh ps [domain]

Domains:
  infra_storage | infra_vector | infra_queue | infra_lineage | infra_portainer | infra_llm | infra_app_elasticsearch | ai_ui | app_vector_ui | agent_api | worker_scan | worker_parse_document | worker_chunk_text | worker_embed_chunks | worker_index_weaviate
USAGE
}

main() {
  local command="${1:-}"
  local domain=""
  local no_build="1"

  shift || true

  case "$command" in
    up)
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --build)
            no_build="0"
            ;;
          *)
            if [[ -z "$domain" ]]; then
              domain="$1"
            else
              echo "Unknown argument for up: $1" >&2
              usage
              exit 1
            fi
            ;;
        esac
        shift
      done
      cmd_up "$domain" "$no_build"
      ;;
    down)
      domain="${1:-}"
      cmd_down "$domain"
      ;;
    wipe)
      cmd_wipe
      ;;
    logs)
      domain="${1:-}"
      cmd_logs "$domain"
      ;;
    ps)
      domain="${1:-}"
      cmd_ps "$domain"
      ;;
    -h|--help|help|"")
      usage
      ;;
    *)
      echo "Unknown command: $command" >&2
      usage
      exit 1
      ;;
  esac
}

main "$@"
