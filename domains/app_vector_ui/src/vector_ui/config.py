import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    weaviate_url: str
    query_timeout_seconds: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            weaviate_url=_required_env("WEAVIATE_URL"),
            query_timeout_seconds=int(os.getenv("WEAVIATE_QUERY_TIMEOUT_SECONDS", "10")),
        )


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
