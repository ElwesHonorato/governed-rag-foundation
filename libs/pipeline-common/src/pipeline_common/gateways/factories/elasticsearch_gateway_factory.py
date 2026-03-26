"""Elasticsearch gateway factory for worker runtime."""

from elasticsearch import Elasticsearch

from pipeline_common.elasticsearch import ELASTICSEARCH_POLICIES
from pipeline_common.gateways.elasticsearch import ElasticsearchApiSettings, ElasticsearchIndexGateway
from pipeline_common.startup.contracts import ElasticsearchIndexingContract


class ElasticsearchIndexGatewayFactory:
    """Create Elasticsearch index gateway from runtime settings and job config."""

    def __init__(
        self,
        *,
        elasticsearch_settings: ElasticsearchApiSettings,
        elasticsearch_config: ElasticsearchIndexingContract,
    ) -> None:
        self.elasticsearch_settings = elasticsearch_settings
        self.elasticsearch_config = elasticsearch_config

    def build(self) -> ElasticsearchIndexGateway:
        """Create Elasticsearch index gateway for one worker."""
        elasticsearch_client = Elasticsearch(
            self.elasticsearch_settings.elasticsearch_url,
            request_timeout=self.elasticsearch_config.request_timeout_seconds,
        )
        return ElasticsearchIndexGateway(
            client=elasticsearch_client,
            index_name=self.elasticsearch_config.index_name,
            index_policy=ELASTICSEARCH_POLICIES[self.elasticsearch_config.policy],
        )
