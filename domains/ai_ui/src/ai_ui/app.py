
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

from ai_infra.ai_backend_client import AiBackendClient
from runtime.provider import SettingsProvider, SettingsRequest
from ai_ui.routes import register_routes


def create_app() -> Flask:
    settings = SettingsProvider(SettingsRequest(frontend_ai_backend=True)).bundle.frontend_ai_backend
    ai_backend_client = AiBackendClient(
        base_url=settings.ai_backend_url,
        timeout_seconds=settings.ai_backend_timeout_seconds,
    )

    app = Flask(__name__)
    register_routes(app=app, settings=settings, ai_backend_client=ai_backend_client)
    return app


app = create_app()


def main() -> int:
    app.run(host="0.0.0.0", port=8000)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
