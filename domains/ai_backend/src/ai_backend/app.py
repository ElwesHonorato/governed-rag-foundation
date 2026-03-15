"""Process startup for the AI backend service."""

from __future__ import annotations

from wsgiref.simple_server import make_server

from ai_backend.app_factory import AiBackendApplicationFactory
from ai_backend.service_factory import AgentPlatformServiceFactory
from runtime.provider import SettingsProvider, SettingsRequest


def main() -> int:
    settings = SettingsProvider(SettingsRequest(backend_ai_backend=True)).bundle.backend_ai_backend
    agent_app = AgentPlatformServiceFactory().build()
    app = AiBackendApplicationFactory(settings=settings, agent_app=agent_app).create()
    with make_server(settings.host, settings.port, app) as server:
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
