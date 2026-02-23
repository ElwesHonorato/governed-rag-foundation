#!/usr/bin/env python3
"""Apply governance entities in DataHub."""

from __future__ import annotations

from src.state_loader import resolve_env
from src.orchestration.governance_applier import GovernanceApplier


def main() -> int:
    """CLI entrypoint for governance apply."""

    return GovernanceApplier(resolve_env()).apply()


if __name__ == "__main__":
    raise SystemExit(main())
