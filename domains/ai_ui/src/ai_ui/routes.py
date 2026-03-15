
from flask import Flask, jsonify, render_template, request

from ai_ui.ai_backend_client import AiBackendClient
from ai_ui.config import Settings


def register_routes(*, app: Flask, settings: Settings, ai_backend_client: AiBackendClient) -> None:

    @app.get("/")
    def root():
        return jsonify(
            {
                "service": "ai-ui",
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
            response, status_code = ai_backend_client.query(payload)
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 502
        return jsonify(response), status_code
