#!/usr/bin/env python3
"""Exercise DataHubLineageClient with a fanout run scenario.

This mirrors the output style and flow of minimal_datahub_test.py while
using the reusable class in pipeline_common.lineage.data_hub.lineage.
"""

from __future__ import annotations

import sys
import time
import uuid
from pathlib import Path

# Make local pipeline-common package importable when run from repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_COMMON_SRC = REPO_ROOT / "libs" / "pipeline-common" / "src"
if str(PIPELINE_COMMON_SRC) not in sys.path:
    sys.path.insert(0, str(PIPELINE_COMMON_SRC))

from datahub.metadata.urns import DatasetUrn
from datahub.metadata.schema_classes import DataProcessRunStatusClass

from pipeline_common.lineage.data_hub import DataHubLineageClient, RunSpec


def build_run_id(label: str) -> str:
    """Build unique run id using timestamp + uuid."""
    return f"{int(time.time() * 1000)}-{label}-{uuid.uuid4()}"


def main() -> int:
    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------
    config = {
        "server": "http://localhost:8081",
        "graphql": "http://localhost:8081/api/graphql",
        "flow_platform": "custom",
        "flow_name": "mock_1_fanout_flow",
        "flow_instance": "PROD",
        "parser_job_name": "worker_parser_fanout_mock_2",
        "chunk_job_name": "worker_chunk_text_fanout_mock_2",
        "embed_job_name": "worker_embed_chunks_fanout_mock_2",
        "platform": "rag-data",
        "env": "PROD",
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
    client = DataHubLineageClient(server=config["server"], token=None)

    # -------------------------------------------------------------------------
    # Worker: worker_parser
    # -------------------------------------------------------------------------
    parser_input = DatasetUrn(
        platform=config["platform"],
        name="02_raw/fanout_case_beta_source_document.raw.json",
        env=config["env"],
    )
    parser_output = DatasetUrn(
        platform=config["platform"],
        name=config["datasets"]["worker_parser"]["output"],
        env=config["env"],
    )

    # -------------------------------------------------------------------------
    # Worker: worker_chunk
    # -------------------------------------------------------------------------
    chunk_output1 = DatasetUrn(
        platform=config["platform"],
        name=config["datasets"]["worker_chunk"]["output1"],
        env=config["env"],
    )
    chunk_output2 = DatasetUrn(
        platform=config["platform"],
        name=config["datasets"]["worker_chunk"]["output2"],
        env=config["env"],
    )

    # -------------------------------------------------------------------------
    # Worker: worker_embed
    # -------------------------------------------------------------------------
    embed_output1 = DatasetUrn(
        platform=config["platform"],
        name=config["datasets"]["worker_embed"]["output1"],
        env=config["env"],
    )
    embed_output2 = DatasetUrn(
        platform=config["platform"],
        name=config["datasets"]["worker_embed"]["output2"],
        env=config["env"],
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
    flow, parser_job = client.upsert_flow_and_job(
        flow_platform=config["flow_platform"],
        flow_name=config["flow_name"],
        flow_instance=config["flow_instance"],
        job_name=config["parser_job_name"],
    )
    _, chunk_job = client.upsert_flow_and_job(
        flow_platform=config["flow_platform"],
        flow_name=config["flow_name"],
        flow_instance=config["flow_instance"],
        job_name=config["chunk_job_name"],
    )
    _, embed_job = client.upsert_flow_and_job(
        flow_platform=config["flow_platform"],
        flow_name=config["flow_name"],
        flow_instance=config["flow_instance"],
        job_name=config["embed_job_name"],
    )
    parser_job_urn = str(parser_job.urn)
    chunk_job_urn = str(chunk_job.urn)
    embed_job_urn = str(embed_job.urn)

    print(f"   DataFlow URN: {flow.urn}")
    print(f"   Parser Job URN: {parser_job_urn}")
    print(f"   Chunk Job URN: {chunk_job_urn}")
    print(f"   Embed Job URN: {embed_job_urn}")

    # -------------------------------------------------------------------------
    # Worker run specs
    # -------------------------------------------------------------------------
    run_worker_parser = RunSpec(
        run_id=build_run_id("parser"),
        attempt=1,
        job_version="git:fanout-beta-parser",
        inputs=[str(parser_input)],
        outputs=[str(parser_output)],
    )
    run_worker_chunk = RunSpec(
        run_id=build_run_id("chunk-fanout"),
        attempt=1,
        job_version="git:fanout-beta-chunk",
        inputs=[str(parser_output)],
        outputs=[str(chunk_output1), str(chunk_output2)],
    )

    # -------------------------------------------------------------------------
    # Worker: worker_embed (branch A)
    # -------------------------------------------------------------------------
    run_worker_embed_a = RunSpec(
        run_id=build_run_id("embed-a"),
        attempt=1,
        job_version="git:fanout-beta-embed-a",
        inputs=[str(chunk_output1)],
        outputs=[str(embed_output1)],
    )

    # -------------------------------------------------------------------------
    # Worker: worker_embed (branch B)
    # -------------------------------------------------------------------------
    run_worker_embed_b = RunSpec(
        run_id=build_run_id("embed-b"),
        attempt=1,
        job_version="git:fanout-beta-embed-b",
        inputs=[str(chunk_output2)],
        outputs=[str(embed_output2)],
    )

    # -------------------------------------------------------------------------
    # Ordered push execution by worker (finish one worker before next)
    # -------------------------------------------------------------------------
    done_dataset_urns: set[str] = set()

    def ensure_datasets(dataset_urns: list[str]) -> None:
        pending = [urn for urn in dataset_urns if urn not in done_dataset_urns]
        if not pending:
            return
        client.upsert_datasets(pending)
        done_dataset_urns.update(pending)

    def push_run(job_urn: str, run_spec: RunSpec, label: str) -> str:
        ensure_datasets(run_spec.inputs + run_spec.outputs)
        dpi_urn = client.emit_dpi_event(
            datajob_urn=job_urn,
            run=run_spec,
            status=DataProcessRunStatusClass.STARTED,
        )
        print(f"   {label} START -> {dpi_urn}")
        dpi_urn = client.emit_dpi_event(
            datajob_urn=job_urn,
            run=run_spec,
            status=DataProcessRunStatusClass.COMPLETE,
        )
        print(f"   {label} COMPLETE -> {dpi_urn}")
        return dpi_urn

    print("2) Emitting DataProcessInstance events in exact push order...")
    emitted_dp_is: set[str] = set()

    print("   Worker: worker_parser")
    emitted_dp_is.add(push_run(parser_job_urn, run_worker_parser, "worker_parser"))

    print("   Worker: worker_chunk")
    emitted_dp_is.add(push_run(chunk_job_urn, run_worker_chunk, "worker_chunk"))

    print("   Worker: worker_embed")
    emitted_dp_is.add(push_run(embed_job_urn, run_worker_embed_a, "worker_embed branch A"))
    emitted_dp_is.add(push_run(embed_job_urn, run_worker_embed_b, "worker_embed branch B"))

    print("   Emitted DPIs:")
    for dpi_urn in sorted(emitted_dp_is):
        print(f"     - {dpi_urn}")

    # -------------------------------------------------------------------------
    # Verification
    # -------------------------------------------------------------------------
    print("3) Quick verification: GraphQL traversal checks...")
    down1 = client.gql_scroll(config["graphql"], str(chunk_output1), "DOWNSTREAM")
    down2 = client.gql_scroll(config["graphql"], str(chunk_output2), "DOWNSTREAM")
    embed_upstream = client.gql_scroll(config["graphql"], embed_job_urn, "UPSTREAM")
    print("   chunk_output1 downstream contains embed_output1:", str(embed_output1) in down1)
    print("   chunk_output2 downstream contains embed_output2:", str(embed_output2) in down2)
    print("   embed job upstream contains chunk_output1:", str(chunk_output1) in embed_upstream)
    print("   embed job upstream contains chunk_output2:", str(chunk_output2) in embed_upstream)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
