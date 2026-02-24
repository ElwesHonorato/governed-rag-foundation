#!/usr/bin/env python3
"""Exercise DataHubRunTimeLineage with a fanout run scenario.

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

from pipeline_common.lineage.data_hub import DataHubRunTimeLineage
from pipeline_common.lineage.data_hub.contracts import DataHubLineageRuntimeConfig, DataHubRuntimeConnectionSettings
from pipeline_common.lineage import DatasetPlatform
from pipeline_common.lineage.pipeline import DataHubPipelineJobs
from pipeline_common.settings import DataHubBootstrapSettings

def main() -> int:
    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------
    bootstrap_settings = DataHubBootstrapSettings.from_env()
    run_suffix = str(time.time_ns())
    config = {
        "server": bootstrap_settings.server,
        "graphql": f"{bootstrap_settings.server}/api/graphql",
        "platform": DatasetPlatform.S3,
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
    parser_client = DataHubRunTimeLineage(
        client_config=DataHubLineageRuntimeConfig(
            connection_settings=DataHubRuntimeConnectionSettings(
                server=bootstrap_settings.server,
                env=bootstrap_settings.env,
                token=bootstrap_settings.token,
                timeout_sec=bootstrap_settings.timeout_sec,
                retry_max_times=bootstrap_settings.retry_max_times,
            ),
            data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_parse_document"),
        ),
    )
    chunk_client = DataHubRunTimeLineage(
        client_config=DataHubLineageRuntimeConfig(
            connection_settings=DataHubRuntimeConnectionSettings(
                server=bootstrap_settings.server,
                env=bootstrap_settings.env,
                token=bootstrap_settings.token,
                timeout_sec=bootstrap_settings.timeout_sec,
                retry_max_times=bootstrap_settings.retry_max_times,
            ),
            data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_chunk_text"),
        ),
    )
    embed_client = DataHubRunTimeLineage(
        client_config=DataHubLineageRuntimeConfig(
            connection_settings=DataHubRuntimeConnectionSettings(
                server=bootstrap_settings.server,
                env=bootstrap_settings.env,
                token=bootstrap_settings.token,
                timeout_sec=bootstrap_settings.timeout_sec,
                retry_max_times=bootstrap_settings.retry_max_times,
            ),
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

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
