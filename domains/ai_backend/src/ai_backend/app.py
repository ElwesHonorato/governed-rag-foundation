"""WSGI entrypoint for the AI backend service."""

from __future__ import annotations

from wsgiref.simple_server import make_server

from agent_platform.startup.service_factory import AgentPlatformServiceFactory
from ai_backend.routes import AiBackendApplication
from runtime.provider import SettingsProvider, SettingsRequest


def create_app() -> AiBackendApplication:
    settings = SettingsProvider(SettingsRequest(backend_ai_backend=True)).bundle.backend_ai_backend
    agent_app = AgentPlatformServiceFactory().build()
    return AiBackendApplication(settings=settings, agent_app=agent_app)


app = create_app()


def main() -> int:
    settings = SettingsProvider(SettingsRequest(backend_ai_backend=True)).bundle.backend_ai_backend
    with make_server(settings.host, settings.port, app) as server:
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
