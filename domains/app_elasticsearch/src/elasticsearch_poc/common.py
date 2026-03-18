"""Shared helpers for the standalone Elasticsearch proof of concept."""

from __future__ import annotations

import json
import os
from pathlib import Path
import time
from typing import Any

from elasticsearch import Elasticsearch

DEFAULT_ELASTICSEARCH_URL = "http://localhost:9201"
DEFAULT_INDEX_NAME = "rag_chunks"
DEFAULT_TIMEOUT_SECONDS = 10.0
WAIT_TIMEOUT_SECONDS = 60.0
WAIT_POLL_SECONDS = 1.0
DEFAULT_S3_ENDPOINT = "http://localhost:9000"
DEFAULT_S3_BUCKET = "rag-data"
DEFAULT_S3_PREFIX = "DEV/04_chunks/"
DEFAULT_S3_ACCESS_KEY = "minio"
DEFAULT_S3_SECRET_KEY = "minio123"


def elasticsearch_url() -> str:
    return os.environ.get("ELASTICSEARCH_POC_URL", DEFAULT_ELASTICSEARCH_URL).strip()


def index_name() -> str:
    return os.environ.get("ELASTICSEARCH_POC_INDEX", DEFAULT_INDEX_NAME).strip()


def build_client() -> Elasticsearch:
    return Elasticsearch(
        elasticsearch_url(),
        request_timeout=DEFAULT_TIMEOUT_SECONDS,
    )


def s3_endpoint() -> str:
    return os.environ.get("ELASTICSEARCH_POC_S3_ENDPOINT", DEFAULT_S3_ENDPOINT).strip()


def s3_bucket() -> str:
    return os.environ.get("ELASTICSEARCH_POC_S3_BUCKET", DEFAULT_S3_BUCKET).strip()


def s3_prefix() -> str:
    return os.environ.get("ELASTICSEARCH_POC_S3_PREFIX", DEFAULT_S3_PREFIX).strip()


def s3_access_key() -> str:
    return os.environ.get("ELASTICSEARCH_POC_S3_ACCESS_KEY", DEFAULT_S3_ACCESS_KEY).strip()


def s3_secret_key() -> str:
    return os.environ.get("ELASTICSEARCH_POC_S3_SECRET_KEY", DEFAULT_S3_SECRET_KEY).strip()


def sample_documents_path() -> Path:
    return Path(__file__).resolve().parents[2] / "sample_data" / "rag_chunks.json"


def load_sample_documents() -> list[dict[str, object]]:
    payload = json.loads(sample_documents_path().read_text())
    if not isinstance(payload, list):
        raise ValueError("sample data must be a JSON list")
    return payload


def normalize_chunk_document(
    *,
    chunk_id: str,
    doc_id: str,
    source_key: str,
    text: str,
    content_type: str,
    created_at: str,
    security_clearance: str,
    source_type: str,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, object]:
    metadata: dict[str, Any] = {
        "security_clearance": security_clearance,
        "source_type": source_type,
    }
    if extra_metadata:
        metadata.update(extra_metadata)
    return {
        "chunk_id": chunk_id,
        "doc_id": doc_id,
        "source_key": source_key,
        "text": text,
        "content_type": content_type,
        "created_at": created_at,
        "metadata": metadata,
    }


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
    print(f"[config] ELASTICSEARCH_POC_URL={elasticsearch_url()}")
    print(f"[config] ELASTICSEARCH_POC_INDEX={index_name()}")


def print_minio_summary() -> None:
    print(f"[config] ELASTICSEARCH_POC_S3_ENDPOINT={s3_endpoint()}")
    print(f"[config] ELASTICSEARCH_POC_S3_BUCKET={s3_bucket()}")
    print(f"[config] ELASTICSEARCH_POC_S3_PREFIX={s3_prefix()}")
