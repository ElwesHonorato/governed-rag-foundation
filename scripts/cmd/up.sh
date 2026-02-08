#!/usr/bin/env bash
set -euo pipefail

cmd_up() {
  local domain="${1:-}"
  local d

  ensure_network
  ensure_localdata_dirs

  while IFS= read -r d; do
    echo "Starting domain: $d"
    compose_domain "$d" up -d --build
  done < <(selected_domains "$domain")
}
