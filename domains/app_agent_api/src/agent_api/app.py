"""WSGI entrypoint for the agent-platform HTTP API."""

from __future__ import annotations

import sys
from pathlib import Path
from wsgiref.simple_server import make_server


def _bootstrap_sys_path() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    path_roots = (
        repo_root / "libs" / "ai_infra" / "src",
        repo_root / "domains" / "agent_platform" / "src",
        repo_root / "domains" / "app_agent_api" / "src",
    )
    for path in path_roots:
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


_bootstrap_sys_path()

from agent_api.config import Settings
from agent_api.routes import AgentApiApplication
from startup.service_factory import AgentPlatformServiceFactory


def create_app() -> AgentApiApplication:
    settings = Settings()
    agent_app = AgentPlatformServiceFactory().build()
    return AgentApiApplication(settings=settings, agent_app=agent_app)


app = create_app()


if __name__ == "__main__":
    settings = Settings()
    with make_server(settings.host, settings.port, app) as server:
        server.serve_forever()
