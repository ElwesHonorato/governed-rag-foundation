"""Process startup for the AI backend service."""

from __future__ import annotations

from wsgiref.simple_server import make_server

from ai_backend.adapters.http.web_application_factory import WebApplicationFactory
from ai_backend.engine_factory import Engine, EngineFactory
from agent_platform.application.execution_runtime_factory import ExecutionRuntimeFactory
from agent_platform.rag.rag_runtime_factory import RagRuntimeFactory
from agent_platform.startup.bootstrap import RuntimeBootstrapper
from agent_platform.startup.startup_assets_factory import StartupAssetsFactory
from runtime.provider import SettingsProvider, SettingsRequest


def main() -> int:
    settings = SettingsProvider(SettingsRequest(backend_ai_backend=True)).bundle.backend_ai_backend
    engine_factory = EngineFactory(
        startup_assets_factory=StartupAssetsFactory(
            bootstrapper=RuntimeBootstrapper()
        ),
        execution_runtime_factory=ExecutionRuntimeFactory(),
        rag_runtime_factory=RagRuntimeFactory(),
    )
    agent_app: Engine = engine_factory.build()
    app = WebApplicationFactory(settings=settings, agent_app=agent_app).create()
    with make_server(settings.host, settings.port, app) as server:
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
