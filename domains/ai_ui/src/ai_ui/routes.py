
from flask import Flask, jsonify, render_template, request

from ai_infra.agent_api_client import AgentApiClient
from ai_ui.settings import FrontendAgentApiSettings


def register_routes(
    *, app: Flask, settings: FrontendAgentApiSettings, agent_api_client: AgentApiClient
) -> None:

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
            response, status_code = agent_api_client.query_grounded_response(payload)
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 502
        return jsonify(response), status_code
