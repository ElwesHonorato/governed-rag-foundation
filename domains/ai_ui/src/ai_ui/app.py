
"""ai-ui Flask application entrypoint.

Purpose:
- Build and expose the HTTP API process used by the RAG application layer.

What this module should do:
- Read API/runtime settings.
- Construct shared clients (for example LLM client) once at startup.
- Create Flask app, register routes, and expose `app` for WSGI/ASGI runners.

Best practices:
- Keep request handling in route modules; keep this file focused on app wiring.
- Keep client initialization explicit and centralized to simplify testing.
- Use a production WSGI server in deployment instead of Flask dev server.
"""

from flask import Flask

from ai_infra.agent_api_client import AgentApiClient
from ai_ui.routes import register_routes
from ai_ui.settings import FrontendAgentApiSettings


def create_app(
    *,
    settings: FrontendAgentApiSettings,
) -> Flask:
    agent_api_client: AgentApiClient = AgentApiClient(
        base_url=settings.agent_api_url,
        timeout_seconds=settings.agent_api_timeout_seconds,
    )

    ai_ui_app: Flask = Flask(__name__)
    register_routes(
        app=ai_ui_app,
        settings=settings,
        agent_api_client=agent_api_client,
    )
    return ai_ui_app


app: Flask = create_app(settings=FrontendAgentApiSettings.from_env())


def main() -> int:
    ai_ui_settings: FrontendAgentApiSettings = FrontendAgentApiSettings.from_env()
    ai_ui_app: Flask = create_app(settings=ai_ui_settings)
    ai_ui_app.run(host="0.0.0.0", port=8000)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
