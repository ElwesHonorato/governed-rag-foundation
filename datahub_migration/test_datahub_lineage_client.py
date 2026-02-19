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

from pipeline_common.lineage.data_hub import DataHubDataFlowBuilder, DataHubLineageClient
from pipeline_common.lineage.data_hub.constants import DataHubStageFlowConfig
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
                "output": "03_processed/fanout_case_beta_source_document.json",
            },
            "worker_chunk": {
                "output1": "04_chunks/fanout_case_beta_branch_a.chunk.json",
                "output2": "04_chunks/fanout_case_beta_branch_b.chunk.json",
            },
            "worker_embed": {
                "output1": "05_embeddings/fanout_case_beta_branch_a.embedding.json",
                "output2": "05_embeddings/fanout_case_beta_branch_b.embedding.json",
            },
        },
    }

    # -------------------------------------------------------------------------
    # Client Initialization
    # -------------------------------------------------------------------------
    parser_client = DataHubLineageClient(
        stage=DataHubStageFlowConfig.WORKER_PARSE_DOCUMENT,
        settings=DataHubBootstrapSettings.from_env(),
    )
    chunk_client = DataHubLineageClient(
        stage=DataHubStageFlowConfig.WORKER_CHUNK_TEXT,
        settings=DataHubBootstrapSettings.from_env(),
    )
    embed_client = DataHubLineageClient(
        stage=DataHubStageFlowConfig.WORKER_EMBED_CHUNKS,
        settings=DataHubBootstrapSettings.from_env(),
    )

    # -------------------------------------------------------------------------
    # Bootstrap DataHub Entities
    # -------------------------------------------------------------------------
    """
    Bootstrap DataHub template entities required for lineage fanout testing.

    This section creates the DataFlow and DataJob hierarchy used by the
    reproduction script before emitting any DataProcessInstance runs.

    Because this script is designed to be **self-contained and repeatable**,
    it performs idempotent upserts on every execution. This differs from
    production architecture, where static metadata creation should occur
    during deployment rather than at runtime.

    The returned URNs are later used to:

    - attach DataProcessInstance runs to their parent DataJobs
    - verify lineage traversal across fanout/fanin scenarios
    - reproduce the Marquez job-lineage mismatch using DataHub semantics
    """
    print("1) Upserting DataFlow + DataJobs (static templates)...")
    flow_builder = DataHubDataFlowBuilder(DataHubStageFlowConfig, DataHubBootstrapSettings.from_env())
    flow_builder.upsert_all()

    print(f"   DataFlow URN: {parser_client.flow_urn}")
    print(f"   Parser Job URN: {parser_client.job_urn}")
    print(f"   Chunk Job URN: {chunk_client.job_urn}")
    print(f"   Embed Job URN: {embed_client.job_urn}")

    # -------------------------------------------------------------------------
    # Ordered push execution by worker (finish one worker before next)
    # -------------------------------------------------------------------------

    print("2) Emitting DataProcessInstance events in exact push order...")
    emitted_dp_is: set[str] = set()

    print("   Worker: worker_parser")
    parser_client.reset_io()
    parser_client.add_input(platform=config["platform"], name="02_raw/fanout_case_beta_source_document.raw.json")
    parser_client.add_output(platform=config["platform"], name=config["datasets"]["worker_parser"]["output"])
    parser_dpi_urn = parser_client.push_run()
    print(f"   worker_parser COMPLETE -> {parser_dpi_urn}")
    emitted_dp_is.add(parser_dpi_urn)

    print("   Worker: worker_chunk")
    chunk_client.reset_io()
    chunk_client.add_input(platform=config["platform"], name=config["datasets"]["worker_parser"]["output"])
    chunk_client.add_output(platform=config["platform"], name=config["datasets"]["worker_chunk"]["output1"])
    chunk_client.add_output(platform=config["platform"], name=config["datasets"]["worker_chunk"]["output2"])
    chunk_dpi_urn = chunk_client.push_run()
    print(f"   worker_chunk COMPLETE -> {chunk_dpi_urn}")
    emitted_dp_is.add(chunk_dpi_urn)

    print("   Worker: worker_embed")
    embed_client.reset_io()
    embed_client.add_input(platform=config["platform"], name=config["datasets"]["worker_chunk"]["output1"])
    embed_client.add_output(platform=config["platform"], name=config["datasets"]["worker_embed"]["output1"])
    embed_a_dpi_urn = embed_client.push_run()
    print(f"   worker_embed-branch-a COMPLETE -> {embed_a_dpi_urn}")
    emitted_dp_is.add(embed_a_dpi_urn)

    embed_client.reset_io()
    embed_client.add_input(platform=config["platform"], name=config["datasets"]["worker_chunk"]["output2"])
    embed_client.add_output(platform=config["platform"], name=config["datasets"]["worker_embed"]["output2"])
    embed_b_dpi_urn = embed_client.push_run()
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
