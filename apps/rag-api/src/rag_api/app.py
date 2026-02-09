
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
