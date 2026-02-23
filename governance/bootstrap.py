#!/usr/bin/env python3
"""Bootstrap static governance entities in DataHub."""

from __future__ import annotations

from src.common import resolve_env
from src.apply import run_bootstrap


def main() -> int:
    """CLI entrypoint that applies only static governance entities."""

    return run_bootstrap(resolve_env())


if __name__ == "__main__":
    raise SystemExit(main())
