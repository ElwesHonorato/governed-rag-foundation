
"""rag-api Flask application entrypoint.

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

from rag_api.config import Settings
from rag_api.llm_client import OllamaClient
from rag_api.routes import register_routes


def create_app() -> Flask:
    settings = Settings()
    llm_client = OllamaClient(
        llm_url=settings.llm_url,
        timeout_seconds=settings.llm_timeout_seconds,
    )

    app = Flask(__name__)
    register_routes(app=app, settings=settings, llm_client=llm_client)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
