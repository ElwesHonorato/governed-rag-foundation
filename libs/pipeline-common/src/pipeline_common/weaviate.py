from __future__ import annotations

import json
from typing import Any
from urllib import request


def _http_json(url: str, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = request.Request(url=url, method=method, data=data, headers=headers)
    with request.urlopen(req, timeout=10) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body else {}


def ensure_schema(weaviate_url: str) -> None:
    schema_url = f"{weaviate_url.rstrip('/')}/v1/schema"
    schema = _http_json(schema_url, "GET")
    classes = {c.get("class") for c in schema.get("classes", [])}
    if "DocumentChunk" in classes:
        return

    _http_json(
        schema_url,
        "POST",
        {
            "class": "DocumentChunk",
            "vectorizer": "none",
            "properties": [
                {"name": "chunk_id", "dataType": ["text"]},
                {"name": "doc_id", "dataType": ["text"]},
                {"name": "chunk_text", "dataType": ["text"]},
                {"name": "source_key", "dataType": ["text"]},
                {"name": "security_clearance", "dataType": ["text"]},
            ],
        },
    )


def _stable_uuid_from_chunk_id(chunk_id: str) -> str:
    normalized = (chunk_id or "").replace("-", "")
    hex32 = (normalized[:32]).ljust(32, "0")
    return (
        f"{hex32[0:8]}-{hex32[8:12]}-{hex32[12:16]}-"
        f"{hex32[16:20]}-{hex32[20:32]}"
    )


def upsert_chunk(weaviate_url: str, *, chunk_id: str, vector: list[float], properties: dict[str, Any]) -> None:
    object_id = _stable_uuid_from_chunk_id(chunk_id)
    url = f"{weaviate_url.rstrip('/')}/v1/objects/{object_id}"
    payload = {
        "class": "DocumentChunk",
        "id": object_id,
        "vector": vector,
        "properties": properties,
    }
    _http_json(url, "PUT", payload)


def verify_query(weaviate_url: str, phrase: str) -> dict[str, Any]:
    url = f"{weaviate_url.rstrip('/')}/v1/graphql"
    gql = {
        "query": (
            "{Get{DocumentChunk(where:{path:[\"chunk_text\"],operator:Like,valueText:\"*"
            + phrase
            + "*\"},limit:3){chunk_id doc_id chunk_text}}}"
        )
    }
    return _http_json(url, "POST", gql)
