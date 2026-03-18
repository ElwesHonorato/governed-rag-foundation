"""Bulk index sample chunk-like documents into Elasticsearch."""

from __future__ import annotations

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from elasticsearch_poc.common import build_client
from elasticsearch_poc.common import index_name
from elasticsearch_poc.common import load_sample_documents
from elasticsearch_poc.common import print_connection_summary
from elasticsearch_poc.common import wait_for_elasticsearch
from elasticsearch_poc.create_index import create_index


def seed_documents(*, client: Elasticsearch, target_index: str) -> int:
    documents = load_sample_documents()
    actions = []
    for document in documents:
        actions.append(
            {
                "_index": target_index,
                "_id": str(document["chunk_id"]),
                "_source": document,
            }
        )
    success_count, _ = bulk(client=client, actions=actions, refresh=True)
    return int(success_count)


def main() -> int:
    print_connection_summary()
    client = build_client()
    wait_for_elasticsearch(client=client)
    target_index = index_name()
    create_index(client=client, target_index=target_index)
    indexed_count = seed_documents(client=client, target_index=target_index)
    print(f"[seed] indexed {indexed_count} document(s) into '{target_index}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
