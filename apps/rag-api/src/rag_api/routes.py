from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from rag_api.config import Settings
from rag_api.llm_client import OllamaClient
from rag_api.services.prompt_service import normalize_prompt, run_prompt


def register_routes(*, app: Flask, settings: Settings, llm_client: OllamaClient) -> None:
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

        try:
            prompt_text = normalize_prompt(payload.get("prompt", ""))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        try:
            result = run_prompt(
                prompt=prompt_text,
                model=settings.llm_model,
                llm_client=llm_client,
            )
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 502

        return jsonify(result)
