#!/usr/bin/env bash
set -euo pipefail

cmd_logs() {
  local domain="${1:-}"

  require_domain_arg "$domain"
  compose_domain "$domain" logs -f --tail=100
}
