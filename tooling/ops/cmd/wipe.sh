#!/usr/bin/env bash
set -euo pipefail

cmd_wipe() {
  local d
  local first="1"

  ui_section "WIPE"
  ui_print warn "This removes containers, volumes, and local data"

  while IFS= read -r d; do
    if [[ "$first" == "0" ]]; then
      ui_space
    fi
    first="0"

    ui_rule
    ui_print action "domain=$d wipe"
    compose_domain "$d" down -v --remove-orphans
    ui_print ok "domain=$d wiped"
  done < <(selected_domains "")

  rm -rf "$LOCALDATA_DIR"
  ui_space
  ui_print ok "local data removed: $LOCALDATA_DIR"
}
