#!/usr/bin/env python3
"""CLI entrypoint for governance apply."""

from __future__ import annotations

from state_loader import resolve_env
from orchestration.governance_applier import GovernanceApplier

def main() -> int:
    """CLI entrypoint for governance apply."""

    return GovernanceApplier(resolve_env()).apply()


if __name__ == "__main__":
    raise SystemExit(main())
