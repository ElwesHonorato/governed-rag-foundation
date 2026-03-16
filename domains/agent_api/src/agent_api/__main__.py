"""Module entrypoint for the agent API service."""

from __future__ import annotations

from agent_api.app import main


if __name__ == "__main__":
    raise SystemExit(main())
