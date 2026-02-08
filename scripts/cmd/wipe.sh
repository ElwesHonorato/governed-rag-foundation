#!/usr/bin/env bash
set -euo pipefail

cmd_wipe() {
  local d

  while IFS= read -r d; do
    echo "Wiping domain: $d"
    compose_domain "$d" down -v --remove-orphans
  done < <(selected_domains "")

  rm -rf "$LOCALDATA_DIR"
  echo "Removed local data: $LOCALDATA_DIR"
}
