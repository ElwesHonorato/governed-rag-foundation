"""WSGI entrypoint for the agent-platform HTTP API."""

from __future__ import annotations

from wsgiref.simple_server import make_server

from agent_platform.startup.service_factory import AgentPlatformServiceFactory
from app_agent_api.config import Settings
from app_agent_api.routes import AgentApiApplication


def create_app() -> AgentApiApplication:
    settings = Settings()
    agent_app = AgentPlatformServiceFactory().build()
    return AgentApiApplication(settings=settings, agent_app=agent_app)


app = create_app()


def main() -> int:
    settings = Settings()
    with make_server(settings.host, settings.port, app) as server:
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
