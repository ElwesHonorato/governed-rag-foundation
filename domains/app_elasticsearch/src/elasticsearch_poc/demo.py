"""Run the end-to-end local Elasticsearch proof-of-concept demo."""

from __future__ import annotations

from pathlib import Path
import subprocess

from elasticsearch_poc.common import build_client
from elasticsearch_poc.common import index_name
from elasticsearch_poc.common import print_connection_summary
from elasticsearch_poc.common import wait_for_elasticsearch
from elasticsearch_poc.create_index import create_index
from elasticsearch_poc.search_documents import run_search
from elasticsearch_poc.seed_documents import seed_documents

REPO_ROOT = Path(__file__).resolve().parents[4]
DOCKER_COMPOSE_PATH = REPO_ROOT / "domains" / "infra_elasticsearch" / "docker-compose.yml"
DEMO_QUERIES = (
    "lineage runtime",
    "security clearance",
)


def start_elasticsearch() -> None:
    command = [
        "docker",
        "compose",
        "-f",
        str(DOCKER_COMPOSE_PATH),
        "up",
        "-d",
    ]
    subprocess.run(command, check=True, cwd=REPO_ROOT)


def main() -> int:
    print("[demo] starting local Elasticsearch infra")
    start_elasticsearch()
    print_connection_summary()

    client = build_client()
    print("[demo] waiting for Elasticsearch to become ready")
    wait_for_elasticsearch(client=client)

    target_index = index_name()
    print(f"[demo] creating index '{target_index}'")
    create_index(client=client, target_index=target_index)

    print("[demo] seeding sample documents")
    indexed_count = seed_documents(client=client, target_index=target_index)
    print(f"[demo] indexed {indexed_count} document(s)")

    for query in DEMO_QUERIES:
        print("")
        print(f"[demo] running example search: {query!r}")
        hits = run_search(
            client=client,
            target_index=target_index,
            query_text=query,
            limit=3,
        )
        print(f"[demo] hits={len(hits)}")
        for hit in hits:
            source = hit.get("_source", {})
            if not isinstance(source, dict):
                continue
            print(
                "  - "
                f"chunk_id={source.get('chunk_id', '')} "
                f"doc_id={source.get('doc_id', '')} "
                f"score={hit.get('_score', 0.0):.4f}"
            )
    print("")
    print("[demo] complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
