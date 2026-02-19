#!/usr/bin/env python3
"""Minimal dataset-to-dataset lineage test using DataHub Python SDK.

Requires:
  pip install acryl-datahub
"""

from __future__ import annotations

import argparse
import sys
import time

import requests


def has_datahub_sdk() -> bool:
    try:
        from datahub.sdk import DataHubClient  # noqa: F401
        from datahub.metadata.urns import DatasetUrn  # noqa: F401
        return True
    except Exception:
        return False


def verify_lineage(endpoint: str, upstream_urn: str, downstream_urn: str) -> tuple[bool, bool]:
    def gql_urns(query: str) -> list[str]:
        response = requests.post(endpoint, json={"query": query}, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if payload.get("errors"):
            raise RuntimeError(f"GraphQL errors: {payload['errors']}")
        results = (
            payload.get("data", {})
            .get("scrollAcrossLineage", {})
            .get("searchResults", [])
        )
        return [item.get("entity", {}).get("urn", "") for item in results]

    q_down = (
        "query { scrollAcrossLineage(input: {"
        f'urn: "{upstream_urn}", direction: DOWNSTREAM, count: 50'
        "}) { searchResults { entity { urn type } } } }"
    )
    q_up = (
        "query { scrollAcrossLineage(input: {"
        f'urn: "{downstream_urn}", direction: UPSTREAM, count: 50'
        "}) { searchResults { entity { urn type } } } }"
    )

    down = gql_urns(q_down)
    up = gql_urns(q_up)
    return downstream_urn in down, upstream_urn in up


def main() -> int:
    parser = argparse.ArgumentParser(description="DataHub SDK dataset lineage minimal test")
    parser.add_argument("--server", default="http://localhost:8081")
    parser.add_argument("--graphql", default="http://localhost:8081/api/graphql")
    parser.add_argument(
        "--upstream1",
        default="04_chunks/a204e8b00fc95a95e854f4a0.part1/5d6fa2bd4c8f9fda94a1b948ae0c5a5db139bc6884acac22705d828b2d1a09bd.chunk.json",
    )
    parser.add_argument(
        "--downstream1",
        default="05_embeddings/a204e8b00fc95a95e854f4a0.part1/5d6fa2bd4c8f9fda94a1b948ae0c5a5db139bc6884acac22705d828b2d1a09bd.embedding.json",
    )
    parser.add_argument(
        "--upstream2",
        default="04_chunks/a204e8b00fc95a95e854f4a0.part2/40672b6cd77dc46285d180c7e0fe9f1c9e0725cfcbd6e12bfe415810b67d0bf8.chunk.json",
    )
    parser.add_argument(
        "--downstream2",
        default="05_embeddings/a204e8b00fc95a95e854f4a0.part2/40672b6cd77dc46285d180c7e0fe9f1c9e0725cfcbd6e12bfe415810b67d0bf8.embedding.json",
    )
    args = parser.parse_args()

    if not has_datahub_sdk():
        print("Missing dependency: acryl-datahub")
        print("Install with: pip install acryl-datahub")
        return 3

    from datahub.sdk import DataHubClient
    from datahub.metadata.urns import DatasetUrn

    client = DataHubClient(server=args.server, token=None)

    u1 = DatasetUrn(platform="rag-data", name=args.upstream1, env="PROD")
    d1 = DatasetUrn(platform="rag-data", name=args.downstream1, env="PROD")
    u2 = DatasetUrn(platform="rag-data", name=args.upstream2, env="PROD")
    d2 = DatasetUrn(platform="rag-data", name=args.downstream2, env="PROD")

    print("Adding 2 dataset lineage edges via SDK...")
    client.lineage.add_lineage(upstream=u1, downstream=d1)
    client.lineage.add_lineage(upstream=u2, downstream=d2)

    print("Verifying via GraphQL lineage traversal...")
    ok1_down = ok1_up = ok2_down = ok2_up = False
    for _ in range(12):
        ok1_down, ok1_up = verify_lineage(args.graphql, str(u1), str(d1))
        ok2_down, ok2_up = verify_lineage(args.graphql, str(u2), str(d2))
        if all([ok1_down, ok1_up, ok2_down, ok2_up]):
            break
        time.sleep(1)

    print(f"edge1 upstream->downstream: {'PASS' if ok1_down else 'FAIL'}")
    print(f"edge1 downstream<-upstream: {'PASS' if ok1_up else 'FAIL'}")
    print(f"edge2 upstream->downstream: {'PASS' if ok2_down else 'FAIL'}")
    print(f"edge2 downstream<-upstream: {'PASS' if ok2_up else 'FAIL'}")

    return 0 if all([ok1_down, ok1_up, ok2_down, ok2_up]) else 2


if __name__ == "__main__":
    sys.exit(main())
