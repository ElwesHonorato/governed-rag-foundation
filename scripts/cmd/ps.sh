#!/usr/bin/env bash
set -euo pipefail

cmd_ps() {
  local domain="${1:-}"
  local d

  while IFS= read -r d; do
    echo "Domain: $d"
    compose_domain "$d" ps
    echo
  done < <(selected_domains "$domain")
}
