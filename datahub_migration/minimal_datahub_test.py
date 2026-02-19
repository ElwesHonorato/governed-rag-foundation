#!/usr/bin/env python3
"""
Reproduce the fanout pattern from the Marquez failed-lineage observation using DataHub:
  1) Producer run emits two chunk outputs from one input.
  2) Consumer job runs twice with different IO sets:
     - run A: chunk1 -> embedding1
     - run B: chunk2 -> embedding2

Requires:
  pip install acryl-datahub requests

Refs:
- DataFlow & DataJob tutorial: https://docs.datahub.com/docs/api/tutorials/dataflow-datajob  :contentReference[oaicite:0]{index=0}
- DataProcessInstance entity (run lifecycle & aspects): https://docs.datahub.com/docs/generated/metamodel/entities/dataprocessinstance :contentReference[oaicite:1]{index=1}
- Graph client: https://docs.datahub.com/docs/python-sdk/clients/graph-client :contentReference[oaicite:2]{index=2}
"""

from __future__ import annotations

import argparse
import sys
import time
import uuid
from dataclasses import dataclass
from typing import Iterable

import requests


def must_import() -> None:
    # SDK v2 entities (DataFlow/DataJob/Dataset) + graph emitter (DPI aspects)
    from datahub.sdk import DataHubClient, DataFlow, DataJob, Dataset  # noqa: F401
    from datahub.ingestion.graph.client import DataHubGraph, DatahubClientConfig  # noqa: F401
    from datahub.emitter.mcp import MetadataChangeProposalWrapper  # noqa: F401
    from datahub.metadata.urns import DatasetUrn  # noqa: F401
    import datahub.metadata.schema_classes as models  # noqa: F401


def gql_scroll(endpoint: str, urn: str, direction: str) -> list[str]:
    q = f"""
    query {{
      scrollAcrossLineage(input: {{
        urn: "{urn}",
        direction: {direction},
        count: 200
      }}) {{
        searchResults {{
          entity {{ urn type }}
        }}
      }}
    }}
    """
    r = requests.post(endpoint, json={"query": q}, timeout=30)
    r.raise_for_status()
    payload = r.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    results = payload.get("data", {}).get("scrollAcrossLineage", {}).get("searchResults", [])
    return [x.get("entity", {}).get("urn", "") for x in results]


@dataclass(frozen=True)
class RunSpec:
    run_id: str
    attempt: int
    job_version: str
    inputs: list[str]
    outputs: list[str]


def upsert_datasets(client, dataset_urns: Iterable[str]) -> None:
    """
    Ensure datasets exist so lineage/run edges don’t fail with
    'Entity ... does not exist, and hence cannot be updated.'
    """
    from datahub.sdk import Dataset
    from datahub.metadata.urns import DatasetUrn

    for urn_str in dataset_urns:
        urn = DatasetUrn.from_string(urn_str)
        client.entities.upsert(
            Dataset(
                platform=urn.platform,
                name=urn.name,
                env=urn.env,
                description="mock_1 dataset created for lineage/run test",
            )
        )


def upsert_flow_and_job(client, *, flow_platform: str, flow_name: str, flow_instance: str, job_name: str):
    """
    Create the static "template" entities.
    """
    from datahub.sdk import DataFlow, DataJob

    flow = DataFlow(
        platform=flow_platform,       # e.g. "custom" / "airflow"
        name=flow_name,               # pipeline id
        platform_instance=flow_instance,  # e.g. "PROD"
        description="mock_1 pipeline for fanout/fanin run lineage testing",
    )
    client.entities.upsert(flow)

    job = DataJob(
        name=job_name,  # stage/task name
        flow=flow,
        description="mock_1 job that produces multiple outputs",
    )
    client.entities.upsert(job)
    return flow, job


def emit_dpi(
    *,
    gms_server: str,
    datajob_urn: str,
    run: RunSpec,
    external_url: str | None = None,
) -> str:
    """
    Emit:
      - dataProcessInstanceProperties (customProperties includes job_version)
      - dataProcessInstanceRelationships.parentTemplate = DataJob URN
      - dataProcessInstanceInput / dataProcessInstanceOutput (per-run IO)
      - dataProcessInstanceRunEvent STARTED, then COMPLETE

    DPI lifecycle statuses documented in DataHub metamodel. :contentReference[oaicite:3]{index=3}
    """
    from datahub.ingestion.graph.client import DataHubGraph, DatahubClientConfig
    from datahub.emitter.mcp import MetadataChangeProposalWrapper
    from datahub.metadata.com.linkedin.pegasus2avro.dataprocess import (
        DataProcessInstanceInput,
        DataProcessInstanceOutput,
    )
    from datahub.metadata.schema_classes import (
        AuditStampClass,
        ChangeTypeClass,
        DataProcessInstancePropertiesClass,
        DataProcessInstanceRelationshipsClass,
        DataProcessInstanceRunEventClass,
        DataProcessRunStatusClass,
        EdgeClass,
    )

    # These aspects are defined in the DataProcessInstance entity. :contentReference[oaicite:4]{index=4}
    # Graph client docs: :contentReference[oaicite:5]{index=5}
    graph = DataHubGraph(DatahubClientConfig(server=gms_server, token=None))

    dpi_urn = f"urn:li:dataProcessInstance:{run.run_id}"
    now_ms = int(time.time() * 1000)

    props = DataProcessInstancePropertiesClass(
        name=run.run_id,
        created=AuditStampClass(
            time=now_ms,
            actor="urn:li:corpuser:datahub",
        ),
        type="BATCH_SCHEDULED",
        externalUrl=external_url,
        customProperties={
            "job_version": run.job_version,
            "attempt": str(run.attempt),
        },
    )

    rel = DataProcessInstanceRelationshipsClass(
        upstreamInstances=[],
        parentTemplate=datajob_urn,
    )

    # Per-run IO edges
    dpi_in = DataProcessInstanceInput(
        inputs=[],
        inputEdges=[EdgeClass(destinationUrn=u) for u in run.inputs],
    )
    dpi_out = DataProcessInstanceOutput(
        outputs=[],
        outputEdges=[EdgeClass(destinationUrn=u) for u in run.outputs],
    )

    started = DataProcessInstanceRunEventClass(
        timestampMillis=now_ms,
        status=DataProcessRunStatusClass.STARTED,
        attempt=run.attempt,
    )

    completed = DataProcessInstanceRunEventClass(
        timestampMillis=now_ms + 1,
        status=DataProcessRunStatusClass.COMPLETE,
        attempt=run.attempt,
    )

    mcps = [
        MetadataChangeProposalWrapper(entityUrn=dpi_urn, aspect=props, changeType=ChangeTypeClass.UPSERT),
        MetadataChangeProposalWrapper(
            entityUrn=dpi_urn,
            entityType="dataProcessInstance",
            aspectName="dataProcessInstanceRelationships",
            aspect=rel,
            changeType=ChangeTypeClass.UPSERT,
        ),
        MetadataChangeProposalWrapper(
            entityUrn=dpi_urn,
            entityType="dataProcessInstance",
            aspectName="dataProcessInstanceInput",
            aspect=dpi_in,
            changeType=ChangeTypeClass.UPSERT,
        ),
        MetadataChangeProposalWrapper(
            entityUrn=dpi_urn,
            entityType="dataProcessInstance",
            aspectName="dataProcessInstanceOutput",
            aspect=dpi_out,
            changeType=ChangeTypeClass.UPSERT,
        ),
        # timeseries events: STARTED then COMPLETE
        MetadataChangeProposalWrapper(
            entityUrn=dpi_urn,
            entityType="dataProcessInstance",
            aspectName="dataProcessInstanceRunEvent",
            aspect=started,
            changeType=ChangeTypeClass.UPSERT,
        ),
        MetadataChangeProposalWrapper(
            entityUrn=dpi_urn,
            entityType="dataProcessInstance",
            aspectName="dataProcessInstanceRunEvent",
            aspect=completed,
            changeType=ChangeTypeClass.UPSERT,
        ),
    ]

    with graph:
        for mcp in mcps:
            graph.emit(mcp)

    return dpi_urn


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="http://localhost:8081", help="GMS server base URL")
    parser.add_argument("--graphql", default="http://localhost:8081/api/graphql", help="GraphQL endpoint")

    parser.add_argument("--flow-platform", default="custom")
    parser.add_argument("--flow-name", default="mock_1_fanout_flow")
    parser.add_argument("--flow-instance", default="PROD")
    parser.add_argument("--chunk-job-name", default="worker_chunk_text_fanout_mock_2")
    parser.add_argument("--embed-job-name", default="worker_embed_chunks_fanout_mock_2")

    parser.add_argument("--input", default="03_processed/fanout_case_beta_source_document.json")
    parser.add_argument("--output1", default="04_chunks/fanout_case_beta_branch_a.chunk.json")
    parser.add_argument("--output2", default="04_chunks/fanout_case_beta_branch_b.chunk.json")
    parser.add_argument("--mapped1", default="05_embeddings/fanout_case_beta_branch_a.embedding.json")
    parser.add_argument("--mapped2", default="05_embeddings/fanout_case_beta_branch_b.embedding.json")

    args = parser.parse_args()

    try:
        must_import()
    except Exception as e:
        print("Missing or incompatible dependency: acryl-datahub")
        print("Install/upgrade with: pip install -U acryl-datahub")
        print("Import error:", e)
        return 3

    from datahub.sdk import DataHubClient
    from datahub.metadata.urns import DatasetUrn

    client = DataHubClient(server=args.server, token=None)

    # Build dataset URNs
    inp = DatasetUrn(platform="rag-data", name=args.input, env="PROD")
    out1 = DatasetUrn(platform="rag-data", name=args.output1, env="PROD")
    out2 = DatasetUrn(platform="rag-data", name=args.output2, env="PROD")
    map1 = DatasetUrn(platform="rag-data", name=args.mapped1, env="PROD")
    map2 = DatasetUrn(platform="rag-data", name=args.mapped2, env="PROD")
    all_ds = [str(x) for x in [inp, out1, out2, map1, map2]]

    print("1) Upserting datasets (so run/lineage edges won't fail)...")
    upsert_datasets(client, all_ds)

    print("2) Upserting DataFlow + DataJobs (static templates)...")
    flow, chunk_job = upsert_flow_and_job(
        client,
        flow_platform=args.flow_platform,
        flow_name=args.flow_name,
        flow_instance=args.flow_instance,
        job_name=args.chunk_job_name,
    )
    _, embed_job = upsert_flow_and_job(
        client,
        flow_platform=args.flow_platform,
        flow_name=args.flow_name,
        flow_instance=args.flow_instance,
        job_name=args.embed_job_name,
    )
    chunk_job_urn = str(chunk_job.urn)
    embed_job_urn = str(embed_job.urn)

    print(f"   DataFlow URN: {flow.urn}")
    print(f"   Chunk Job URN: {chunk_job_urn}")
    print(f"   Embed Job URN: {embed_job_urn}")

    # Reproduce the observed fanout pattern:
    # - one producer run creates two chunk outputs
    # - same embed job runs twice with different input/output pairs
    ts_ms = int(time.time() * 1000)
    run_chunk = RunSpec(
        run_id=f"{ts_ms}-chunk-fanout-{uuid.uuid4()}",
        attempt=1,
        job_version="git:fanout-beta-chunk",
        inputs=[str(inp)],
        outputs=[str(out1), str(out2)],
    )
    run_a = RunSpec(
        run_id=f"{ts_ms}-a-{uuid.uuid4()}",
        attempt=1,
        job_version="git:fanout-beta-embed-a",
        inputs=[str(out1)],
        outputs=[str(map1)],
    )
    run_b = RunSpec(
        run_id=f"{ts_ms}-b-{uuid.uuid4()}",
        attempt=1,
        job_version="git:fanout-beta-embed-b",
        inputs=[str(out2)],
        outputs=[str(map2)],
    )

    print("3) Emitting DataProcessInstance runs with per-run IO...")
    dpi_chunk = emit_dpi(gms_server=args.server, datajob_urn=chunk_job_urn, run=run_chunk)
    dpi_a = emit_dpi(gms_server=args.server, datajob_urn=embed_job_urn, run=run_a)
    dpi_b = emit_dpi(gms_server=args.server, datajob_urn=embed_job_urn, run=run_b)

    print(f"   Emitted DPI Chunk: {dpi_chunk}")
    print(f"   Emitted DPI A: {dpi_a}")
    print(f"   Emitted DPI B: {dpi_b}")

    print("4) Quick verification: GraphQL traversal checks...")
    down1 = gql_scroll(args.graphql, str(out1), "DOWNSTREAM")
    down2 = gql_scroll(args.graphql, str(out2), "DOWNSTREAM")
    embed_upstream = gql_scroll(args.graphql, embed_job_urn, "UPSTREAM")
    print("   out1 downstream contains map1:", str(map1) in down1)
    print("   out2 downstream contains map2:", str(map2) in down2)
    print("   embed job upstream contains out1:", str(out1) in embed_upstream)
    print("   embed job upstream contains out2:", str(out2) in embed_upstream)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
