
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
from runtime.provider import SettingsProvider, SettingsRequest
from ai_ui.routes import register_routes


def create_app() -> Flask:
    settings = SettingsProvider(SettingsRequest(frontend_agent_api=True)).bundle.frontend_agent_api
    agent_api_client = AgentApiClient(
        base_url=settings.agent_api_url,
        timeout_seconds=settings.agent_api_timeout_seconds,
    )

    app = Flask(__name__)
    register_routes(app=app, settings=settings, agent_api_client=agent_api_client)
    return app


app = create_app()


def main() -> int:
    app.run(host="0.0.0.0", port=8000)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
