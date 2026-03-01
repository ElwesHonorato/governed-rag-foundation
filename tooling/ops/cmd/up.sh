#!/usr/bin/env bash
set -euo pipefail

cmd_up() {
  local domain="${1:-}"
  local d
  local first="1"

  ui_section "UP"
  ui_print info "Preparing network and local data directories"
  ensure_network
  ensure_localdata_dirs

  while IFS= read -r d; do
    if [[ "$first" == "0" ]]; then
      ui_space
    fi
    first="0"

    ui_rule
    ui_print action "domain=$d start"
    compose_domain "$d" up -d --build --remove-orphans
    ui_print ok "domain=$d ready"
  done < <(selected_domains "$domain")
}
