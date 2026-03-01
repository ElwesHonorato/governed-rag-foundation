#!/usr/bin/env bash
set -euo pipefail

cmd_down() {
  local domain="${1:-}"
  local d
  local first="1"

  ui_section "DOWN"

  while IFS= read -r d; do
    if [[ "$first" == "0" ]]; then
      ui_space
    fi
    first="0"

    ui_rule
    ui_print action "domain=$d stop"
    compose_domain "$d" down
    ui_print ok "domain=$d stopped"
  done < <(selected_domains "$domain")
}
