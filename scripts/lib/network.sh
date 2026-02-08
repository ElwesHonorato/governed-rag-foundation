#!/usr/bin/env bash
set -euo pipefail

ensure_network() {
  if ! docker network inspect "$STACK_NETWORK" >/dev/null 2>&1; then
    docker network create "$STACK_NETWORK" >/dev/null
    echo "Created network: $STACK_NETWORK"
  fi
}
