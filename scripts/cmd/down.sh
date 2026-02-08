#!/usr/bin/env bash
set -euo pipefail

cmd_down() {
  local domain="${1:-}"
  local d

  while IFS= read -r d; do
    echo "Stopping domain: $d"
    compose_domain "$d" down
  done < <(selected_domains "$domain")
}
