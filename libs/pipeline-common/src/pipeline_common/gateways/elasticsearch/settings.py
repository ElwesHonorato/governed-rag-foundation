from dataclasses import dataclass

from pipeline_common.helpers.config import _required_env


@dataclass(frozen=True)
class ElasticsearchApiSettings:
    """Runtime settings for the Elasticsearch query API."""

    host: str
    port: int
    elasticsearch_url: str

    @classmethod
    def from_env(cls) -> "ElasticsearchApiSettings":
        """Load Elasticsearch query API settings from environment."""
        return cls(
            host=_required_env("APP_ELASTICSEARCH_HOST"),
            port=int(_required_env("APP_ELASTICSEARCH_PORT")),
            elasticsearch_url=_required_env("ELASTICSEARCH_URL"),
        )
