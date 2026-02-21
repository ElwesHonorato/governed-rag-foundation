#!/usr/bin/env python3
"""Bootstrap static governance entities in DataHub."""

from __future__ import annotations

from src.common import parse_args
from src.apply import run_apply


def main() -> int:
    """CLI entrypoint that applies only static governance entities."""

    args = parse_args()
    return run_apply(args.env, static_only=True)


if __name__ == "__main__":
    raise SystemExit(main())
