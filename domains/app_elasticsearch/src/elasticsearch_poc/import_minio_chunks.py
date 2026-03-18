"""Import real chunk artifacts from MinIO into the Elasticsearch spike index."""

from __future__ import annotations

import json
from typing import Any

import boto3
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from elasticsearch_poc.common import build_client
from elasticsearch_poc.common import index_name
from elasticsearch_poc.common import normalize_chunk_document
from elasticsearch_poc.common import print_connection_summary
from elasticsearch_poc.common import print_minio_summary
from elasticsearch_poc.common import s3_access_key
from elasticsearch_poc.common import s3_bucket
from elasticsearch_poc.common import s3_endpoint
from elasticsearch_poc.common import s3_prefix
from elasticsearch_poc.common import s3_secret_key
from elasticsearch_poc.common import wait_for_elasticsearch
from elasticsearch_poc.create_index import create_index


def build_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=s3_endpoint(),
        aws_access_key_id=s3_access_key(),
        aws_secret_access_key=s3_secret_key(),
    )


def list_chunk_keys(*, s3_client: Any, bucket: str, prefix: str) -> list[str]:
    paginator = s3_client.get_paginator("list_objects_v2")
    keys: list[str] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        contents = page.get("Contents", [])
        if not isinstance(contents, list):
            continue
        for entry in contents:
            key = str(entry.get("Key", ""))
            if key.endswith(".json"):
                keys.append(key)
    return keys


def read_chunk_payload(*, s3_client: Any, bucket: str, key: str) -> dict[str, Any]:
    response = s3_client.get_object(Bucket=bucket, Key=key)
    body = response["Body"].read()
    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"chunk artifact must be a JSON object: {key}")
    return payload


def document_from_chunk_artifact(*, object_key: str, payload: dict[str, Any]) -> dict[str, object]:
    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError(f"chunk artifact metadata must be an object: {object_key}")

    root_doc_metadata = metadata.get("root_doc_metadata", {})
    if not isinstance(root_doc_metadata, dict):
        raise ValueError(f"chunk artifact root_doc_metadata must be an object: {object_key}")

    content_metadata = metadata.get("content_metadata", {})
    if not isinstance(content_metadata, dict):
        raise ValueError(f"chunk artifact content_metadata must be an object: {object_key}")

    content = payload.get("content", {})
    if not isinstance(content, dict):
        raise ValueError(f"chunk artifact content must be an object: {object_key}")

    extra_metadata = {
        "stage_source_key": object_key,
        "root_source_uri": str(root_doc_metadata.get("uri", "")),
        "offsets_start": int(content_metadata.get("offsets_start", 0)),
        "offsets_end": int(content_metadata.get("offsets_end", 0)),
        "chunk_text_hash": str(content_metadata.get("chunk_text_hash", "")),
    }

    return normalize_chunk_document(
        chunk_id=str(content_metadata.get("chunk_id", "")),
        doc_id=str(root_doc_metadata.get("doc_id", "")),
        source_key=object_key,
        text=str(content.get("data", "")),
        content_type=str(root_doc_metadata.get("content_type", "application/json")),
        created_at=str(root_doc_metadata.get("timestamp", "")),
        security_clearance=str(root_doc_metadata.get("security_clearance", "")),
        source_type=str(root_doc_metadata.get("source_type", "")),
        extra_metadata=extra_metadata,
    )


def import_minio_chunks(
    *,
    client: Elasticsearch,
    s3_client: Any,
    target_index: str,
    bucket: str,
    prefix: str,
) -> int:
    keys = list_chunk_keys(s3_client=s3_client, bucket=bucket, prefix=prefix)
    if not keys:
        print(f"[import-minio] no JSON chunk artifacts found under s3://{bucket}/{prefix}")
        return 0

    actions = []
    for key in keys:
        document = document_from_chunk_artifact(
            object_key=key,
            payload=read_chunk_payload(s3_client=s3_client, bucket=bucket, key=key),
        )
        actions.append(
            {
                "_index": target_index,
                "_id": str(document["chunk_id"]),
                "_source": document,
            }
        )
    success_count, _ = bulk(client=client, actions=actions, refresh=True)
    print(f"[import-minio] indexed {success_count} document(s) from s3://{bucket}/{prefix}")
    return int(success_count)


def main() -> int:
    print_connection_summary()
    print_minio_summary()
    client = build_client()
    wait_for_elasticsearch(client=client)

    target_index = index_name()
    create_index(client=client, target_index=target_index)
    import_minio_chunks(
        client=client,
        s3_client=build_s3_client(),
        target_index=target_index,
        bucket=s3_bucket(),
        prefix=s3_prefix(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
