"""HTTP handlers for Elasticsearch retrieval API endpoints."""

from __future__ import annotations

from dataclasses import asdict
from http import HTTPStatus

from pipeline_common.gateways.elasticsearch import ElasticsearchGateway
from pipeline_common.http import JsonResponse
from pipeline_common.settings import ElasticsearchApiSettings

class RetrieveHttpHandler:
    """Build JSON responses for retrieval HTTP endpoints."""

    def __init__(
        self,
        *,
        settings: ElasticsearchApiSettings,
        gateway: ElasticsearchGateway,
    ) -> None:
        self._settings = settings
        self._gateway = gateway

    def get_health(self) -> JsonResponse:
        return JsonResponse(
            payload={
                "service": "app-elasticsearch",
                "status": "ok",
                "settings": asdict(self._settings),
            },
            status=HTTPStatus.OK,
        )

    def retrieve(self, body: dict[str, object]) -> JsonResponse:
        query_text = str(body.get("query", "")).strip()
        limit = int(body.get("limit", 5))
        hits = self._gateway.search(query_text=query_text, limit=limit)
        return JsonResponse(
            payload={"query": query_text, "limit": limit, "hits": hits},
            status=HTTPStatus.OK,
        )

    def not_found(self, *, path: str) -> JsonResponse:
        return JsonResponse(
            payload={"error": "not_found", "path": path},
            status=HTTPStatus.NOT_FOUND,
        )
