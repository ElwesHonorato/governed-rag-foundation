from dataclasses import dataclass

from pipeline_common.helpers.config import _optional_env, _required_env


@dataclass(frozen=True)
class ElasticsearchApiSettings:
    """Runtime settings for the Elasticsearch query API."""

    host: str
    port: int
    elasticsearch_url: str
    elasticsearch_index: str

    @classmethod
    def from_env(cls) -> "ElasticsearchApiSettings":
        """Load Elasticsearch query API settings from environment."""
        return cls(
            host=_optional_env("APP_ELASTICSEARCH_HOST", "0.0.0.0"),
            port=int(_optional_env("APP_ELASTICSEARCH_PORT", "8081")),
            elasticsearch_url=_required_env("ELASTICSEARCH_URL"),
            elasticsearch_index=_optional_env("ELASTICSEARCH_INDEX", "rag_chunks"),
        )
