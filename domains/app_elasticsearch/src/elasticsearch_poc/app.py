"""Process startup for the Elasticsearch retrieval API.

This module is the composition root of the Elasticsearch API.

Responsibilities:
- Load environment-driven settings
- Wire infrastructure dependencies for Elasticsearch retrieval
- Construct the application service
- Assemble the HTTP layer (handlers, router, application)
- Start the WSGI server

Nothing here should contain business logic, only wiring.
"""

from __future__ import annotations

from wsgiref.simple_server import make_server

from pipeline_common.gateways.elasticsearch import ElasticsearchGateway
from pipeline_common.settings import ElasticsearchApiSettings, SettingsProvider, SettingsRequest

from elasticsearch_poc.adapters.http.application import ElasticsearchApiApplication
from elasticsearch_poc.adapters.http.retrieve_http_handler import RetrieveHttpHandler
from elasticsearch_poc.adapters.http.router import ElasticsearchApiRouter
from pipeline_common.http import WsgiRequestNormalizer


def main() -> int:
    """Start the local Elasticsearch query API process."""
    settings_bundle = SettingsProvider(SettingsRequest(elasticsearch_api=True)).bundle
    api_settings: ElasticsearchApiSettings = settings_bundle.elasticsearch_api

    gateway = ElasticsearchGateway(
        url=api_settings.elasticsearch_url,
        index_name=api_settings.elasticsearch_index,
    )

    handlers = RetrieveHttpHandler(
        settings=api_settings,
        gateway=gateway,
    )
    request_normalizer = WsgiRequestNormalizer()
    router = ElasticsearchApiRouter(handlers=handlers)
    app = ElasticsearchApiApplication(
        request_normalizer=request_normalizer,
        router=router,
    )

    with make_server(api_settings.host, api_settings.port, app) as server:
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
