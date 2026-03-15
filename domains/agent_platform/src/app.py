"""Entrypoint for the agent-platform CLI."""

from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap_sys_path() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    ai_infra_src = repo_root / "libs" / "ai_infra" / "src"
    agent_src = repo_root / "domains" / "agent_platform" / "src"
    for path in (ai_infra_src, agent_src):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def main(argv: list[str] | None = None) -> int:
    _bootstrap_sys_path()
    from cli.agent_cli import main as cli_main

    return cli_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
