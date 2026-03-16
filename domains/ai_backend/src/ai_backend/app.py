"""Process startup for the AI backend service."""

from __future__ import annotations

from wsgiref.simple_server import make_server

from ai_backend.adapters.http.web_application_factory import WebApplicationFactory
from ai_backend.engine_factory import Engine, EngineFactory
from runtime.provider import SettingsProvider, SettingsRequest


def main() -> int:
    settings = SettingsProvider(SettingsRequest(backend_ai_backend=True)).bundle.backend_ai_backend
    agent_app: Engine = EngineFactory().build()
    app = WebApplicationFactory(settings=settings, agent_app=agent_app).create()
    with make_server(settings.host, settings.port, app) as server:
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
