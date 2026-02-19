#!/usr/bin/env python3
"""Minimal dataset-to-dataset lineage test against local DataHub GraphQL.

This script adds one lineage edge using updateLineage and verifies it via
scrollAcrossLineage queries.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from typing import Any


def run_graphql(endpoint: str, query: str, timeout: int = 30) -> dict[str, Any]:
    payload = json.dumps({"query": query})
    cmd = [
        "curl",
        "-sS",
        "-X",
        "POST",
        endpoint,
        "-H",
        "Content-Type: application/json",
        "--data",
        payload,
    ]
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"curl failed ({proc.returncode}): {proc.stderr.strip()}")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON from GraphQL: {proc.stdout[:500]}") from exc

    if data.get("errors"):
        raise RuntimeError(f"GraphQL errors: {json.dumps(data['errors'])}")
    return data


def lineage_urns(endpoint: str, urn: str, direction: str, count: int = 50) -> list[str]:
    query = (
        "query { scrollAcrossLineage(input: {"
        f'urn: "{urn}", direction: {direction}, count: {count}'
        "}) { searchResults { entity { urn type } } } }"
    )
    data = run_graphql(endpoint, query)
    results = data.get("data", {}).get("scrollAcrossLineage", {}).get("searchResults", [])
    return [item.get("entity", {}).get("urn", "") for item in results]


def main() -> int:
    parser = argparse.ArgumentParser(description="Add + verify one dataset lineage edge in DataHub")
    parser.add_argument("--endpoint", default="http://localhost:8081/api/graphql")
    parser.add_argument(
        "--upstream",
        default=(
            "urn:li:dataset:(urn:li:dataPlatform:rag-data,"
            "04_chunks/a204e8b00fc95a95e854f4a0.part1/"
            "5d6fa2bd4c8f9fda94a1b948ae0c5a5db139bc6884acac22705d828b2d1a09bd.chunk.json,PROD)"
        ),
    )
    parser.add_argument(
        "--downstream",
        default=(
            "urn:li:dataset:(urn:li:dataPlatform:rag-data,"
            "05_embeddings/a204e8b00fc95a95e854f4a0.part1/"
            "5d6fa2bd4c8f9fda94a1b948ae0c5a5db139bc6884acac22705d828b2d1a09bd.embedding.json,PROD)"
        ),
    )
    args = parser.parse_args()

    print("Adding lineage edge:")
    print(f"  upstream   = {args.upstream}")
    print(f"  downstream = {args.downstream}")

    mutation = (
        "mutation { updateLineage(input: {"
        "edgesToAdd: [{"
        f'upstreamUrn: "{args.upstream}", downstreamUrn: "{args.downstream}"'
        "}], edgesToRemove: []"
        "}) }"
    )
    mutation_result = run_graphql(args.endpoint, mutation)
    print(f"Mutation result: {json.dumps(mutation_result)}")

    ok1 = False
    ok2 = False
    down: list[str] = []
    up: list[str] = []
    for _ in range(8):
        down = lineage_urns(args.endpoint, args.upstream, "DOWNSTREAM")
        up = lineage_urns(args.endpoint, args.downstream, "UPSTREAM")
        ok1 = args.downstream in down
        ok2 = args.upstream in up
        if ok1 and ok2:
            break
        time.sleep(1)

    print("Verification:")
    print(f"  upstream -> downstream visible: {'PASS' if ok1 else 'FAIL'}")
    print(f"  downstream <- upstream visible: {'PASS' if ok2 else 'FAIL'}")

    if not ok1:
        print("  downstream query returned:")
        for urn in down:
            print(f"    - {urn}")
    if not ok2:
        print("  upstream query returned:")
        for urn in up:
            print(f"    - {urn}")

    return 0 if (ok1 and ok2) else 2


if __name__ == "__main__":
    sys.exit(main())
