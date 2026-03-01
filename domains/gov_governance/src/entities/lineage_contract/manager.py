#!/usr/bin/env python3
"""Lineage contract governance manager."""

from __future__ import annotations

from typing import Any

from entities.shared.context import LineageContractManagerContext
from entities.shared.ports import GovernanceCatalogWriterPort


class LineageContractManager:
    """Apply lineage contract edges to existing jobs."""

    def __init__(self, governance_def_ctx: LineageContractManagerContext) -> None:
        """Store lineage context and governance catalog writer."""

        self.governance_def_ctx = governance_def_ctx
        self._governance_writer: GovernanceCatalogWriterPort = governance_def_ctx.governance_writer

    def apply(self, pipelines: list[dict[str, Any]]) -> None:
        """Upsert DataJob inlets/outlets for each lineage contract entry."""

        for pipeline in pipelines:
            contracts = {c["job"]: c for c in pipeline.get("lineage_contract", [])}
            for job in pipeline.get("jobs", []):
                contract = contracts.get(job["id"])
                if contract is None:
                    continue

                inlets = [self.governance_def_ctx.dataset_urns[ds_id] for ds_id in contract.get("inputs", [])]
                outlets = [self.governance_def_ctx.dataset_urns[ds_id] for ds_id in contract.get("outputs", [])]

                flow_def = pipeline["flow"]
                self._governance_writer.upsert_job(
                    flow_platform=flow_def["platform"],
                    flow_id=flow_def["id"],
                    env=self.governance_def_ctx.env,
                    job_id=job["id"],
                    description=job.get("description"),
                    custom_properties=job.get("custom_properties", {}),
                    domain=self.governance_def_ctx.domain_urns[job["domain"]],
                    owners=[
                        self.governance_def_ctx.group_urns[group_id]
                        for group_id in job.get("owners", [])
                    ],
                    inlets=inlets,
                    outlets=outlets,
                )
                print(f"upserted lineage contract for job {job['id']} (inputs={len(inlets)} outputs={len(outlets)})")
