"""Endpoint handlers for the AI backend."""

from __future__ import annotations

from http import HTTPStatus

from ai_backend.responses import JsonResponse
from ai_backend.service_factory import AgentPlatformApp
from runtime.provider import BackendAIBackendSettings


class AiBackendHandlers:
    """Endpoint orchestration for AI backend routes."""

    def __init__(self, *, settings: BackendAIBackendSettings, agent_app: AgentPlatformApp) -> None:
        self._settings = settings
        self._agent_app = agent_app

    def get_health(self) -> JsonResponse:
        return JsonResponse(
            payload={"service": "ai-backend", "status": "ok", "settings": self._settings.to_dict},
            status=HTTPStatus.OK,
        )

    def list_capabilities(self) -> JsonResponse:
        return JsonResponse(
            payload=[item.to_dict() for item in self._agent_app.capability_registry.list_capabilities()],
            status=HTTPStatus.OK,
        )

    def list_skills(self) -> JsonResponse:
        return JsonResponse(
            payload=sorted(self._agent_app.skill_registry.keys()),
            status=HTTPStatus.OK,
        )

    def create_run(self, body: dict[str, object]) -> JsonResponse:
        objective = str(body.get("objective", "")).strip()
        skill_name = str(body.get("skill_name", "analyze_repository")).strip()
        run = self._agent_app.run_objective(objective=objective, skill_name=skill_name)
        return JsonResponse(payload=run.to_dict(), status=HTTPStatus.CREATED)

    def create_evaluation(self, body: dict[str, object]) -> JsonResponse:
        run_id = str(body.get("run_id", "")).strip()
        run = self._agent_app.run_store.load_run(run_id)
        evaluation = self._agent_app.evaluation_runner.evaluate(run)
        return JsonResponse(payload=evaluation.to_dict(), status=HTTPStatus.CREATED)

    def query_rag(self, body: dict[str, object]) -> JsonResponse:
        response = self._agent_app.rag_service.respond(body)
        return JsonResponse(payload=response.to_dict(), status=HTTPStatus.OK)
