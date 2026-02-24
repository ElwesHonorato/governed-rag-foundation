#!/usr/bin/env python3
"""Exercise DataHubLineageClient with a fanout run scenario.

This mirrors the output style and flow of minimal_datahub_test.py while
using the reusable class in pipeline_common.lineage.data_hub.lineage.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Make local pipeline-common package importable when run from repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_COMMON_SRC = REPO_ROOT / "libs" / "pipeline-common" / "src"
if str(PIPELINE_COMMON_SRC) not in sys.path:
    sys.path.insert(0, str(PIPELINE_COMMON_SRC))

from pipeline_common.lineage.data_hub import DataHubLineageClient
from pipeline_common.lineage.data_hub.contracts import DataHubLineageRuntimeConfig
from pipeline_common.lineage.pipeline import DataHubPipelineJobs
from pipeline_common.settings import DataHubBootstrapSettings


def wait_for_lineage_contains(
    *,
    client: DataHubLineageClient,
    root_urn: str,
    direction: str,
    expected_urn: str,
    max_attempts: int = 12,
    sleep_seconds: float = 1.0,
) -> bool:
    """Retry lineage traversal until expected URN appears or attempts are exhausted."""
    for _ in range(max_attempts):
        connected = client.gql_scroll(root_urn, direction)
        if expected_urn in connected:
            return True
        time.sleep(sleep_seconds)
    return False


def main() -> int:
    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------
    bootstrap_settings = DataHubBootstrapSettings.from_env()
    run_suffix = str(time.time_ns())
    config = {
        "server": bootstrap_settings.server,
        "graphql": f"{bootstrap_settings.server}/api/graphql",
        "platform": "rag-data",
        "env": bootstrap_settings.env,
        "datasets": {
            "worker_parser": {
                "input": f"02_raw/clean_lineage_{run_suffix}_source_document.raw.json",
                "output": f"03_processed/clean_lineage_{run_suffix}_source_document.json",
            },
            "worker_chunk": {
                "output1": f"04_chunks/clean_lineage_{run_suffix}_branch_a.chunk.json",
                "output2": f"04_chunks/clean_lineage_{run_suffix}_branch_b.chunk.json",
            },
            "worker_embed": {
                "output1": f"05_embeddings/clean_lineage_{run_suffix}_branch_a.embedding.json",
                "output2": f"05_embeddings/clean_lineage_{run_suffix}_branch_b.embedding.json",
            },
        },
    }

    # -------------------------------------------------------------------------
    # Static templates precondition
    # -------------------------------------------------------------------------
    print("1) Assuming DataFlow + DataJobs templates already upserted by governance apply.")

    # -------------------------------------------------------------------------
    # Ordered push execution by worker (finish one worker before next)
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # Client Initialization
    # -------------------------------------------------------------------------
    parser_client = DataHubLineageClient(
        client_config=DataHubLineageRuntimeConfig(
            bootstrap_settings={
                "server": bootstrap_settings.server,
                "env": bootstrap_settings.env,
                "token": bootstrap_settings.token,
            },
            data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_parse_document"),
        ),
    )
    chunk_client = DataHubLineageClient(
        client_config=DataHubLineageRuntimeConfig(
            bootstrap_settings={
                "server": bootstrap_settings.server,
                "env": bootstrap_settings.env,
                "token": bootstrap_settings.token,
            },
            data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_chunk_text"),
        ),
    )
    embed_client = DataHubLineageClient(
        client_config=DataHubLineageRuntimeConfig(
            bootstrap_settings={
                "server": bootstrap_settings.server,
                "env": bootstrap_settings.env,
                "token": bootstrap_settings.token,
            },
            data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_embed_chunks"),
        ),
    )

    print("2) Emitting DataProcessInstance events in exact push order...")
    emitted_dp_is: set[str] = set()

    print("   Worker: worker_parser")
    parser_client.start_run()
    parser_client.add_input(platform=config["platform"], name=config["datasets"]["worker_parser"]["input"])
    parser_client.add_output(platform=config["platform"], name=config["datasets"]["worker_parser"]["output"])
    parser_dpi_urn = parser_client.complete_run()
    print(f"   worker_parser COMPLETE -> {parser_dpi_urn}")
    emitted_dp_is.add(parser_dpi_urn)

    print("   Worker: worker_chunk")
    chunk_client.start_run()
    chunk_client.add_input(platform=config["platform"], name=config["datasets"]["worker_parser"]["output"])
    chunk_client.add_output(platform=config["platform"], name=config["datasets"]["worker_chunk"]["output1"])
    chunk_client.add_output(platform=config["platform"], name=config["datasets"]["worker_chunk"]["output2"])
    chunk_dpi_urn = chunk_client.complete_run()
    print(f"   worker_chunk COMPLETE -> {chunk_dpi_urn}")
    emitted_dp_is.add(chunk_dpi_urn)

    print("   Worker: worker_embed")
    embed_client.start_run()
    embed_client.add_input(platform=config["platform"], name=config["datasets"]["worker_chunk"]["output1"])
    embed_client.add_output(platform=config["platform"], name=config["datasets"]["worker_embed"]["output1"])
    embed_a_dpi_urn = embed_client.complete_run()
    print(f"   worker_embed-branch-a COMPLETE -> {embed_a_dpi_urn}")
    emitted_dp_is.add(embed_a_dpi_urn)

    embed_client.start_run()
    embed_client.add_input(platform=config["platform"], name=config["datasets"]["worker_chunk"]["output2"])
    embed_client.add_output(platform=config["platform"], name=config["datasets"]["worker_embed"]["output2"])
    embed_b_dpi_urn = embed_client.complete_run()
    print(f"   worker_embed-branch-b COMPLETE -> {embed_b_dpi_urn}")
    emitted_dp_is.add(embed_b_dpi_urn)

    print("   Emitted DPIs:")
    for dpi_urn in sorted(emitted_dp_is):
        print(f"     - {dpi_urn}")

    # -------------------------------------------------------------------------
    # Verification
    # -------------------------------------------------------------------------
    print("3) Quick verification: GraphQL traversal checks...")
    chunk_output1_urn = str(
        parser_client.dataset_urn(
            platform=config["platform"],
            name=config["datasets"]["worker_chunk"]["output1"],
        )
    )
    chunk_output2_urn = str(
        parser_client.dataset_urn(
            platform=config["platform"],
            name=config["datasets"]["worker_chunk"]["output2"],
        )
    )
    embed_output1_urn = str(
        parser_client.dataset_urn(
            platform=config["platform"],
            name=config["datasets"]["worker_embed"]["output1"],
        )
    )
    embed_output2_urn = str(
        parser_client.dataset_urn(
            platform=config["platform"],
            name=config["datasets"]["worker_embed"]["output2"],
        )
    )

    down1_ok = wait_for_lineage_contains(
        client=parser_client,
        root_urn=chunk_output1_urn,
        direction="DOWNSTREAM",
        expected_urn=embed_output1_urn,
    )
    down2_ok = wait_for_lineage_contains(
        client=parser_client,
        root_urn=chunk_output2_urn,
        direction="DOWNSTREAM",
        expected_urn=embed_output2_urn,
    )
    dpi_upstream_a_ok = wait_for_lineage_contains(
        client=parser_client,
        root_urn=embed_a_dpi_urn,
        direction="UPSTREAM",
        expected_urn=chunk_output1_urn,
    )
    dpi_upstream_b_ok = wait_for_lineage_contains(
        client=parser_client,
        root_urn=embed_b_dpi_urn,
        direction="UPSTREAM",
        expected_urn=chunk_output2_urn,
    )
    print("   chunk_output1 downstream contains embed_output1:", down1_ok)
    print("   chunk_output2 downstream contains embed_output2:", down2_ok)
    print("   embed DPI A upstream contains chunk_output1:", dpi_upstream_a_ok)
    print("   embed DPI B upstream contains chunk_output2:", dpi_upstream_b_ok)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
