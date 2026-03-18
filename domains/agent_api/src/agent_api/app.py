"""Process startup for the agent API service.

This module is the composition root of the Agent API.

Responsibilities:
- Load environment-driven settings
- Build runtime configuration for the agent engine
- Wire all infrastructure dependencies (LLM, retrieval, embedder)
- Construct the agent execution engine
- Assemble the HTTP layer (handlers, router, application)
- Start the WSGI server

Nothing here should contain business logic — only wiring.
"""

from __future__ import annotations

from wsgiref.simple_server import make_server

from ai_infra.retrieval.deterministic_hash_embedder import (
    DeterministicHashEmbedder,
)

# --- HTTP layer components (pure adapters) ---
from agent_api.adapters.http.application import AgentApiApplication
from agent_api.adapters.http.handlers import AgentApiHandlers
from agent_api.adapters.http.request_normalization import WsgiRequestNormalizer
from agent_api.adapters.http.router import AgentApiRouter
from agent_api.adapters.http.web_application_factory import WebApplicationFactory

# --- Engine + gateway composition ---
from agent_api.startup.engine_factory import (
    AgentApiGatewayFactories,
    AgentAPIEngineFactory,
)

# --- Infrastructure clients ---
from agent_platform.clients.llm.ollama_client import OllamaClient

# --- Gateway factories (bridge infra → domain) ---
from agent_platform.startup.contracts import LLMConfig, RetrievalConfig
from agent_platform.startup.llm_gateway_factory import LLMGatewayFactory
from agent_platform.startup.retrieval_gateway_factory import RetrievalGatewayFactory

# --- Settings / configuration ---
from agent_settings.settings import (
    AgentApiSettings,
    EnvironmentSettingsProvider,
    SettingsBundle,
    SettingsRequest,
)


def main() -> int:
    # ---------------------------------------------------------------------
    # 1. Load settings from environment / configuration sources
    # ---------------------------------------------------------------------
    # SettingsBundle is a strongly-typed aggregation of all required configs
    # for this process (agent_api, llm, retrieval).
    agent_settings: SettingsBundle = EnvironmentSettingsProvider(
        SettingsRequest(agent_api=True, llm=True, retrieval=True)
    ).bundle
    llm_config = LLMConfig(
        settings=agent_settings.llm,
        llm_timeout_seconds=30,
    )
    retrieval_config = RetrievalConfig(
        settings=agent_settings.retrieval,
        embedding_dim=32,
        retrieval_limit=5,
    )

    # ---------------------------------------------------------------------
    # 2. Build infrastructure gateways (LLM + retrieval)
    # ---------------------------------------------------------------------
    # LLM client is the concrete external dependency (Ollama in this case).
    llm_client = OllamaClient(
        llm_url=llm_config.settings.llm_url,
        timeout_seconds=llm_config.llm_timeout_seconds,
    )
    retrieval_embedder = DeterministicHashEmbedder(
        retrieval_config.embedding_dim
    )

    # Gateway factories adapt infrastructure clients into domain-facing interfaces.
    gateway_factories = AgentApiGatewayFactories(
        llm=LLMGatewayFactory(client=llm_client),
        retrieval=RetrievalGatewayFactory(retrieval_embedder=retrieval_embedder),
    )

    # ---------------------------------------------------------------------
    # 3. Construct the agent execution engine
    # ---------------------------------------------------------------------
    # This wires:
    # - retrieval embedder (vectorization strategy)
    # - gateways (LLM + retrieval access)
    # - runtime settings (policies/config)
    engine_factory = AgentAPIEngineFactory(
        gateway_factories=gateway_factories,
        retrieval_config=retrieval_config,
    )

    # Build the actual runtime agent application (core execution unit)
    agent_app = engine_factory.build()

    # ---------------------------------------------------------------------
    # 4. Assemble HTTP layer (adapter → domain boundary)
    # ---------------------------------------------------------------------
    agent_api_settings: AgentApiSettings = agent_settings.agent_api

    # Handlers translate HTTP requests into domain-level calls
    handlers = AgentApiHandlers(
        settings=agent_api_settings,
        agent_app=agent_app,
    )

    # Normalizer ensures incoming WSGI requests are converted
    # into a consistent internal request format
    request_normalizer = WsgiRequestNormalizer()

    # Router maps HTTP routes → handlers
    router = AgentApiRouter(handlers=handlers)

    # Web application factory assembles the WSGI application
    agent_api_app: AgentApiApplication = WebApplicationFactory(
        request_normalizer=request_normalizer,
        router=router,
    ).create()

    # ---------------------------------------------------------------------
    # 5. Start HTTP server (WSGI - development server)
    # ---------------------------------------------------------------------
    # NOTE: wsgiref is suitable for local/dev usage.
    # Replace with a production server (gunicorn/uvicorn) in real deployments.
    with make_server(
        agent_api_settings.host,
        agent_api_settings.port,
        agent_api_app,
    ) as server:
        server.serve_forever()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
