"""Process startup for the agent API service."""

from __future__ import annotations

from wsgiref.simple_server import make_server

from agent_api.adapters.http.application import AgentApiApplication
from agent_api.adapters.http.web_application_factory import WebApplicationFactory
from agent_api.startup.engine_factory import (
    EngineFactory,
    EngineGatewayFactories,
    EngineRuntimeFactories,
    EngineStartupServices,
)
from agent_api.startup.runtime_settings import AgentApiConfigFactory
from agent_platform.agent_runtime.execution_runtime_factory import (
    ExecutionRuntimeFactory,
)
from agent_platform.clients.llm.ollama_client import OllamaClient
from agent_platform.grounded_response.grounded_response_factory import (
    GroundedResponseFactory,
)
from agent_platform.startup.bootstrap import RuntimeBootstrapper
from agent_platform.startup.command_gateway_factory import CommandGatewayFactory
from agent_platform.startup.filesystem_gateway_factory import (
    FilesystemGatewayFactory,
)
from agent_platform.startup.local_state_stores_factory import LocalStateStoresFactory
from agent_platform.startup.llm_gateway_factory import LLMGatewayFactory
from agent_platform.startup.retrieval_gateway_factory import RetrievalGatewayFactory
from agent_platform.startup.retrieval_embedder_factory import (
    RetrievalEmbedderFactory,
)
from agent_platform.startup.vector_gateway_factory import VectorGatewayFactory
from agent_settings.settings import (
    AgentApiSettings,
    EnvironmentSettingsProvider,
    SettingsBundle,
    SettingsRequest,
)


def main() -> int:
    agent_settings: SettingsBundle = EnvironmentSettingsProvider(
        SettingsRequest(agent_api=True, llm=True, retrieval=True)
    ).bundle
    runtime_settings = AgentApiConfigFactory().build(agent_settings)
    engine_factory = EngineFactory(
        startup_services=EngineStartupServices(
            bootstrapper=RuntimeBootstrapper(),
            retrieval_embedder_factory=RetrievalEmbedderFactory(),
            local_state_stores_factory=LocalStateStoresFactory(),
        ),
        gateway_factories=EngineGatewayFactories(
            filesystem=FilesystemGatewayFactory(),
            command=CommandGatewayFactory(),
            vector=VectorGatewayFactory(),
            llm=LLMGatewayFactory(
                client=OllamaClient(
                    llm_url=agent_settings.llm.llm_url,
                    timeout_seconds=agent_settings.llm.llm_timeout_seconds,
                )
            ),
            retrieval=RetrievalGatewayFactory(),
        ),
        runtime_factories=EngineRuntimeFactories(
            execution=ExecutionRuntimeFactory(),
            grounded_response=GroundedResponseFactory(),
        ),
        settings=runtime_settings,
    )
    agent_api_settings: AgentApiSettings = agent_settings.agent_api
    agent_api_app: AgentApiApplication = WebApplicationFactory(
        settings=agent_api_settings,
        agent_app=engine_factory.build(),
    ).create()
    with make_server(
        agent_api_settings.host,
        agent_api_settings.port,
        agent_api_app,
    ) as server:
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
