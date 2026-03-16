"""Process startup for the agent API service."""

from __future__ import annotations

from wsgiref.simple_server import make_server

from agent_api.adapters.http.web_application_factory import WebApplicationFactory
from agent_api.engine_factory import Engine, EngineFactory
from agent_api.settings import (
    AgentApiSettingsProvider,
    AgentApiSettings,
)
from agent_platform.agent_runtime.execution_runtime_factory import (
    ExecutionRuntimeFactory,
)
from agent_platform.grounded_response.grounded_response_factory import (
    GroundedResponseFactory,
)
from agent_platform.startup.bootstrap import RuntimeBootstrapper
from agent_platform.startup.local_state_stores_factory import LocalStateStoresFactory
from agent_platform.startup.retrieval_composition import RetrievalCompositionFactory
from agent_platform.startup.runtime_settings import (
    AgentPlatformConfigFactory,
)
from agent_platform.startup.startup_assets_factory import StartupAssetsFactory


def _serve(*, settings: AgentApiSettings, agent_app: Engine) -> int:
    app = WebApplicationFactory(settings=settings, agent_app=agent_app).create()
    with make_server(settings.host, settings.port, app) as server:
        server.serve_forever()
    return 0


def main() -> int:
    engine_factory = EngineFactory(
        startup_assets_factory=StartupAssetsFactory(
            bootstrapper=RuntimeBootstrapper(),
            retrieval_composition_factory=RetrievalCompositionFactory(),
            local_state_stores_factory=LocalStateStoresFactory(),
            settings=AgentPlatformConfigFactory().build(),
        ),
        execution_runtime_factory=ExecutionRuntimeFactory(),
        grounded_response_factory=GroundedResponseFactory(),
    )
    return _serve(
        settings=AgentApiSettingsProvider().load(),
        agent_app=engine_factory.build(),
    )


if __name__ == "__main__":
    raise SystemExit(main())
