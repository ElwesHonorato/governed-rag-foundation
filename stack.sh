#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$ROOT_DIR/scripts/lib/core.sh"
source "$ROOT_DIR/scripts/lib/network.sh"
source "$ROOT_DIR/scripts/lib/compose.sh"
source "$ROOT_DIR/scripts/cmd/up.sh"
source "$ROOT_DIR/scripts/cmd/down.sh"
source "$ROOT_DIR/scripts/cmd/logs.sh"
source "$ROOT_DIR/scripts/cmd/ps.sh"
source "$ROOT_DIR/scripts/cmd/wipe.sh"

usage() {
  cat <<'USAGE'
Usage:
  ./stack.sh up [domain]
  ./stack.sh down [domain]
  ./stack.sh wipe
  ./stack.sh logs <domain>
  ./stack.sh ps [domain]

Domains:
  storage | vector | queue | lineage | portainer | llm | app | worker_scan | worker_parse_document | worker_chunk_text | worker_embed_chunks | worker_index_weaviate | worker_manifest | worker_metrics
USAGE
}

main() {
  local command="${1:-}"
  local domain="${2:-}"

  case "$command" in
    up)
      cmd_up "$domain"
      ;;
    down)
      cmd_down "$domain"
      ;;
    wipe)
      cmd_wipe
      ;;
    logs)
      cmd_logs "$domain"
      ;;
    ps)
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
