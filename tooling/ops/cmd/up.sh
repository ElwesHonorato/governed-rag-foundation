#!/usr/bin/env bash
set -euo pipefail

cmd_up() {
  local domain="${1:-}"
  local no_build="${2:-0}"
  local d
  local first="1"
  local compose_args=(
    up
    -d
    --remove-orphans
  )

  if [[ "$no_build" == "0" ]]; then
    compose_args+=(--build)
  fi

  ui_section "UP"
  ui_print info "Preparing network and local data directories"
  if [[ "$no_build" == "1" ]]; then
    ui_print info "Build disabled by default (pass --build to rebuild)"
  fi
  ensure_network
  ensure_localdata_dirs

  while IFS= read -r d; do
    if [[ "$first" == "0" ]]; then
      ui_space
    fi
    first="0"

    ui_rule
    ui_print action "domain=$d start"
    compose_domain "$d" "${compose_args[@]}"
    ui_print ok "domain=$d ready"
  done < <(selected_domains "$domain")
}
