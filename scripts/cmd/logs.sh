#!/usr/bin/env bash
set -euo pipefail

logs_print_header() {
  local domain="$1"
  ui_section "LOGS"
  ui_print info "domain=$domain"
  ui_print info "mode=follow tail=100 timestamps=on"
  ui_print warn "press Ctrl+C to stop"
  ui_space
}

logs_print_services() {
  local domain="$1"
  local services service
  services="$(compose_domain "$domain" config --services)"

  if [[ -z "$services" ]]; then
    return
  fi

  ui_print info "services:"
  while IFS= read -r service; do
    [[ -z "$service" ]] && continue
    ui_print action "service=$service"
  done <<< "$services"
  ui_space
}

logs_colorize_stream() {
  local use_color="0"
  ui_use_color && use_color="1"

  awk -v use_color="$use_color" '
    function color_for_prefix(prefix,    n) {
      n = 31 + (length(prefix) % 6)
      return sprintf("\033[%sm", n)
    }
    {
      if (use_color != "1") {
        print $0
        next
      }

      split($0, parts, " \\| ")
      prefix = parts[1]

      if (prefix == "") {
        print $0
        next
      }

      color = color_for_prefix(prefix)
      reset = "\033[0m"
      sub(/^([^|]+)\| /, color "&" reset, $0)
      print $0
    }
  '
}

cmd_logs() {
  local domain="${1:-}"

  require_domain_arg "$domain"
  logs_print_header "$domain"
  logs_print_services "$domain"
  compose_domain "$domain" logs -f --tail=100 --timestamps 2>&1 | logs_colorize_stream
}
