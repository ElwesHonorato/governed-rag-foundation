"""Run simple text search against the Elasticsearch spike index."""

from __future__ import annotations

import argparse

from elasticsearch import Elasticsearch

from elasticsearch_poc.common import build_client
from elasticsearch_poc.common import index_name
from elasticsearch_poc.common import preview_text
from elasticsearch_poc.common import print_connection_summary
from elasticsearch_poc.common import wait_for_elasticsearch


def run_search(
    *,
    client: Elasticsearch,
    target_index: str,
    query_text: str,
    limit: int,
) -> list[dict[str, object]]:
    response = client.search(
        index=target_index,
        size=limit,
        query={
            "match": {
                "text": {
                    "query": query_text,
                }
            }
        },
    )
    hits = response.get("hits", {}).get("hits", [])
    if not isinstance(hits, list):
        return []
    return hits


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search the Elasticsearch spike index")
    parser.add_argument("query", help="text query to run against the text field")
    parser.add_argument("--limit", type=int, default=5, help="maximum number of hits to print")
    return parser


def main() -> int:
    args = build_argument_parser().parse_args()
    print_connection_summary()
    client = build_client()
    wait_for_elasticsearch(client=client)

    hits = run_search(
        client=client,
        target_index=index_name(),
        query_text=args.query,
        limit=args.limit,
    )
    print(f"[search] query={args.query!r} hits={len(hits)}")
    if not hits:
        print("[search] no matching documents")
        return 0

    for hit in hits:
        source = hit.get("_source", {})
        if not isinstance(source, dict):
            continue
        print("")
        print(f"- chunk_id={source.get('chunk_id', '')}")
        print(f"  doc_id={source.get('doc_id', '')}")
        print(f"  source_key={source.get('source_key', '')}")
        print(f"  score={hit.get('_score', 0.0):.4f}")
        print(f"  text={preview_text(str(source.get('text', '')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
