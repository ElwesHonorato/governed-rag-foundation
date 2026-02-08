#!/usr/bin/env bash
set -euo pipefail

ps_colorize_table() {
  local use_color="0"
  ui_use_color && use_color="1"

  awk -v use_color="$use_color" '
    function paint(code, text,    reset) {
      if (use_color != "1") {
        return text
      }
      reset = "\033[0m"
      return sprintf("\033[%sm%s%s", code, text, reset)
    }

    {
      line = $0

      if (line ~ /^NAME[[:space:]]+IMAGE[[:space:]]+COMMAND[[:space:]]+SERVICE[[:space:]]+CREATED[[:space:]]+STATUS[[:space:]]+PORTS$/) {
        print paint("1;36", line)
        next
      }

      if (line ~ /no containers to show/) {
        print paint("33", line)
        next
      }

      gsub(/Up [^,]+/, paint("32", "&"), line)
      gsub(/\(healthy\)/, paint("32", "&"), line)
      gsub(/\(unhealthy\)/, paint("31", "&"), line)
      gsub(/Exited \([0-9]+\)/, paint("31", "&"), line)
      gsub(/Restarting/, paint("33", "&"), line)
      gsub(/Dead/, paint("31", "&"), line)
      gsub(/Created/, paint("33", "&"), line)

      print line
    }
  '
}

cmd_ps() {
  local domain="${1:-}"
  local d
  local first="1"

  ui_section "PS"

  while IFS= read -r d; do
    if [[ "$first" == "0" ]]; then
      ui_space
    fi
    first="0"

    ui_rule
    ui_print info "domain=$d"
    compose_domain "$d" ps | ps_colorize_table
  done < <(selected_domains "$domain")
}
