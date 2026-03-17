"""Process startup for the agent API service."""

from __future__ import annotations

from wsgiref.simple_server import make_server

from agent_api.adapters.http.application import AgentApiApplication
from agent_api.adapters.http.web_application_factory import WebApplicationFactory
from agent_api.startup.engine_factory import (
    AgentApiGatewayFactories,
    AgentAPIEngineFactory,
)
from agent_api.startup.runtime_settings import AgentAPIConfigEngineFactory
from agent_platform.clients.llm.ollama_client import OllamaClient
from agent_platform.startup.llm_gateway_factory import LLMGatewayFactory
from agent_platform.startup.retrieval_gateway_factory import RetrievalGatewayFactory
from agent_platform.startup.embedder_factory import EmbedderFactory
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
    runtime_settings = AgentAPIConfigEngineFactory().build(agent_settings)
    engine_factory = AgentAPIEngineFactory(
        retrieval_embedder_factory=EmbedderFactory(),
        gateway_factories=AgentApiGatewayFactories(
            llm=LLMGatewayFactory(
                client=OllamaClient(
                    llm_url=agent_settings.llm.llm_url,
                    timeout_seconds=agent_settings.llm.llm_timeout_seconds,
                )
            ),
            retrieval=RetrievalGatewayFactory(),
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
