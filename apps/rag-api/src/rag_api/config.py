
import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    llm_url: str = field(init=False)
    llm_model: str = field(init=False)
    llm_timeout_seconds: int = field(init=False)
    weaviate_url: str = field(init=False)
    embedding_dim: int = field(init=False)
    retrieval_limit: int = field(init=False)
    broker_url: str = field(init=False)
    s3_endpoint: str = field(init=False)
    marquez_url: str = field(init=False)

    def __post_init__(self) -> None:
        timeout_raw = self._required_env("LLM_TIMEOUT_SECONDS")
        try:
            llm_timeout = int(timeout_raw)
        except ValueError as exc:
            raise ValueError("LLM_TIMEOUT_SECONDS must be an integer") from exc

        self.llm_url = self._required_env("LLM_URL")
        self.llm_model = self._required_env("LLM_MODEL")
        self.llm_timeout_seconds = llm_timeout
        self.weaviate_url = self._required_env("WEAVIATE_URL")
        self.embedding_dim = self._required_int_env("EMBEDDING_DIM")
        self.retrieval_limit = int(os.getenv("WEAVIATE_QUERY_DEFAULTS_LIMIT", "5"))
        self.broker_url = self._required_env("BROKER_URL")
        self.s3_endpoint = self._required_env("S3_ENDPOINT")
        self.marquez_url = self._required_env("MARQUEZ_URL")

    def dependencies_payload(self) -> dict[str, str]:
        return {
            "weaviate": self.weaviate_url,
            "broker": self.broker_url,
            "s3": self.s3_endpoint,
            "marquez": self.marquez_url,
            "llm": self.llm_url,
            "llm_model": self.llm_model,
        }

    def _required_env(self, name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"{name} is not configured")
        return value.strip()

    def _required_int_env(self, name: str) -> int:
        raw_value = self._required_env(name)
        try:
            return int(raw_value)
        except ValueError as exc:
            raise ValueError(f"{name} must be an integer") from exc
