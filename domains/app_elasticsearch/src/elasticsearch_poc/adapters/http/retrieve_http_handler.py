"""HTTP handlers for Elasticsearch retrieval API endpoints."""

from __future__ import annotations

from dataclasses import asdict
from http import HTTPStatus

from elasticsearch_poc.adapters.http.contracts import RetrieveRequest
from pipeline_common.elasticsearch import ElasticsearchRetrievedDocumentList
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

    def retrieve(self, request: RetrieveRequest) -> JsonResponse:
        response: ElasticsearchRetrievedDocumentList = self._gateway.search(
            query_text=request.query,
            limit=request.limit,
        )
        return JsonResponse(
            payload=response.to_dict,
            status=HTTPStatus.OK,
        )

    def not_found(self, *, path: str) -> JsonResponse:
        return JsonResponse(
            payload={"error": "not_found", "path": path},
            status=HTTPStatus.NOT_FOUND,
        )
