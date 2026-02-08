from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from rag_api.config import Settings
from rag_api.llm_client import OllamaClient
from rag_api.services.prompt_service import PromptService


def register_routes(*, app: Flask, settings: Settings, llm_client: OllamaClient) -> None:
    prompt_service = PromptService(llm_client=llm_client, model=settings.llm_model)

    @app.get("/")
    def root():
        return jsonify(
            {
                "service": "rag-api",
                "status": "ok",
                "dependencies": settings.dependencies_payload(),
            }
        )

    @app.get("/ui")
    def ui():
        return render_template("ui.html")

    @app.post("/prompt")
    def prompt():
        payload = request.get_json(silent=True) or {}
        response, status_code = prompt_service.handle_prompt(payload)
        return jsonify(response), status_code
