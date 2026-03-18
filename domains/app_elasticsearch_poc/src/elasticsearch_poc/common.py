"""Shared helpers for the standalone Elasticsearch proof of concept."""

from __future__ import annotations

import json
import os
from pathlib import Path
import time

from elasticsearch import Elasticsearch

DEFAULT_ELASTICSEARCH_URL = "http://localhost:9201"
DEFAULT_INDEX_NAME = "rag_chunks"
DEFAULT_TIMEOUT_SECONDS = 10.0
WAIT_TIMEOUT_SECONDS = 60.0
WAIT_POLL_SECONDS = 1.0


def elasticsearch_url() -> str:
    return os.environ.get("ELASTICSEARCH_URL", DEFAULT_ELASTICSEARCH_URL).strip()


def index_name() -> str:
    return os.environ.get("ELASTICSEARCH_INDEX", DEFAULT_INDEX_NAME).strip()


def build_client() -> Elasticsearch:
    return Elasticsearch(
        elasticsearch_url(),
        request_timeout=DEFAULT_TIMEOUT_SECONDS,
    )


def sample_documents_path() -> Path:
    return Path(__file__).resolve().parents[2] / "sample_data" / "rag_chunks.json"


def load_sample_documents() -> list[dict[str, object]]:
    payload = json.loads(sample_documents_path().read_text())
    if not isinstance(payload, list):
        raise ValueError("sample data must be a JSON list")
    return payload


def wait_for_elasticsearch(*, client: Elasticsearch) -> None:
    deadline = time.time() + WAIT_TIMEOUT_SECONDS
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            if client.ping():
                return
        except Exception as exc:  # pragma: no cover - local retry path
            last_error = exc
        time.sleep(WAIT_POLL_SECONDS)
    if last_error is None:
        raise RuntimeError("Elasticsearch did not become ready before timeout")
    raise RuntimeError(f"Elasticsearch did not become ready: {last_error}")


def preview_text(text: str, *, max_chars: int = 140) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3] + "..."


def print_connection_summary() -> None:
    print(f"[config] ELASTICSEARCH_URL={elasticsearch_url()}")
    print(f"[config] ELASTICSEARCH_INDEX={index_name()}")

