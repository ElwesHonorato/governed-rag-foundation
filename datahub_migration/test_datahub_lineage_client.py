#!/usr/bin/env python3
"""Exercise DataHubLineageClient with a fanout run scenario.

This mirrors the output style and flow of minimal_datahub_test.py while
using the reusable class in pipeline_common.lineage.data_hub.lineage.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make local pipeline-common package importable when run from repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_COMMON_SRC = REPO_ROOT / "libs" / "pipeline-common" / "src"
if str(PIPELINE_COMMON_SRC) not in sys.path:
    sys.path.insert(0, str(PIPELINE_COMMON_SRC))

from pipeline_common.lineage.data_hub import DataHubLineageClient
from pipeline_common.lineage.data_hub.contracts import DataHubLineageRuntimeConfig
from pipeline_common.lineage.contracts import DataHubFlowConfig
from pipeline_common.settings import DataHubBootstrapSettings


def main() -> int:
    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------
    bootstrap_settings = DataHubBootstrapSettings.from_env()
    config = {
        "server": bootstrap_settings.server,
        "graphql": f"{bootstrap_settings.server}/api/graphql",
        "platform": "rag-data",
        "env": bootstrap_settings.env,
        "datasets": {
            "worker_parser": {
                "output": "03_processed/fanout_case_delta_20260219_source_document.json",
            },
            "worker_chunk": {
                "output1": "04_chunks/fanout_case_delta_20260219_branch_a.chunk.json",
                "output2": "04_chunks/fanout_case_delta_20260219_branch_b.chunk.json",
            },
            "worker_embed": {
                "output1": "05_embeddings/fanout_case_delta_20260219_branch_a.embedding.json",
                "output2": "05_embeddings/fanout_case_delta_20260219_branch_b.embedding.json",
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
            server=bootstrap_settings.server,
            env=bootstrap_settings.env,
            token=bootstrap_settings.token,
            stage=DataHubFlowConfig(
                flow_id="governed-rag",
                job_id="worker_parse_document",
                flow_platform="custom",
                flow_name="governed-rag",
                flow_instance=bootstrap_settings.env,
                job_name="worker_parse_document",
            ),
        ),
    )
    chunk_client = DataHubLineageClient(
        client_config=DataHubLineageRuntimeConfig(
            server=bootstrap_settings.server,
            env=bootstrap_settings.env,
            token=bootstrap_settings.token,
            stage=DataHubFlowConfig(
                flow_id="governed-rag",
                job_id="worker_chunk_text",
                flow_platform="custom",
                flow_name="governed-rag",
                flow_instance=bootstrap_settings.env,
                job_name="worker_chunk_text",
            ),
        ),
    )
    embed_client = DataHubLineageClient(
        client_config=DataHubLineageRuntimeConfig(
            server=bootstrap_settings.server,
            env=bootstrap_settings.env,
            token=bootstrap_settings.token,
            stage=DataHubFlowConfig(
                flow_id="governed-rag",
                job_id="worker_embed_chunks",
                flow_platform="custom",
                flow_name="governed-rag",
                flow_instance=bootstrap_settings.env,
                job_name="worker_embed_chunks",
            ),
        ),
    )

    print("2) Emitting DataProcessInstance events in exact push order...")
    emitted_dp_is: set[str] = set()

    print("   Worker: worker_parser")
    parser_client.start_run()
    parser_client.add_input(platform=config["platform"], name="02_raw/fanout_case_delta_20260219_source_document.raw.json")
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

    down1 = parser_client.gql_scroll(config["graphql"], chunk_output1_urn, "DOWNSTREAM")
    down2 = parser_client.gql_scroll(config["graphql"], chunk_output2_urn, "DOWNSTREAM")
    embed_job_urn = embed_client.job_urn
    embed_upstream = parser_client.gql_scroll(config["graphql"], embed_job_urn, "UPSTREAM")
    print("   chunk_output1 downstream contains embed_output1:", embed_output1_urn in down1)
    print("   chunk_output2 downstream contains embed_output2:", embed_output2_urn in down2)
    print("   embed job upstream contains chunk_output1:", chunk_output1_urn in embed_upstream)
    print("   embed job upstream contains chunk_output2:", chunk_output2_urn in embed_upstream)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
