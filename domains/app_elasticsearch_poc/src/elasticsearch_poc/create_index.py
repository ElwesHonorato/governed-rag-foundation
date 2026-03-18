"""Create the standalone Elasticsearch spike index."""

from __future__ import annotations

from elasticsearch import Elasticsearch

from elasticsearch_poc.common import build_client
from elasticsearch_poc.common import index_name
from elasticsearch_poc.common import print_connection_summary
from elasticsearch_poc.common import wait_for_elasticsearch


def create_index(*, client: Elasticsearch, target_index: str) -> None:
    if client.indices.exists(index=target_index):
        print(f"[create-index] index '{target_index}' already exists")
        return

    mapping = {
        "mappings": {
            "properties": {
                "chunk_id": {"type": "keyword"},
                "doc_id": {"type": "keyword"},
                "source_key": {"type": "keyword"},
                "text": {"type": "text"},
                "content_type": {"type": "keyword"},
                "created_at": {"type": "date"},
                "metadata": {
                    "properties": {
                        "security_clearance": {"type": "keyword"},
                        "source_type": {"type": "keyword"},
                    }
                },
            }
        }
    }
    client.indices.create(index=target_index, **mapping)
    print(f"[create-index] created index '{target_index}'")


def main() -> int:
    print_connection_summary()
    client = build_client()
    wait_for_elasticsearch(client=client)
    create_index(client=client, target_index=index_name())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
