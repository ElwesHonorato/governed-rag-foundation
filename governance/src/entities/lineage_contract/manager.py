#!/usr/bin/env python3
"""Lineage contract governance manager."""

from __future__ import annotations

from typing import Any

from entities.flows_jobs.manager import FlowJobManager
from entities.shared.context import GovernanceContext


class LineageContractManager:
    """Apply lineage contract edges to existing jobs."""

    def __init__(self, ctx: GovernanceContext) -> None:
        """Store context and helper manager for DataJob construction."""

        self.ctx = ctx
        self._flow_job_manager = FlowJobManager(ctx)

    def apply(self, pipelines: list[dict[str, Any]]) -> None:
        """Upsert DataJob inlets/outlets for each lineage contract entry."""

        for pipeline in pipelines:
            contracts = {c["job"]: c for c in pipeline.get("lineage_contract", [])}
            for job in pipeline.get("jobs", []):
                contract = contracts.get(job["id"])
                if contract is None:
                    continue

                inlets = [self.ctx.refs.dataset_urns[ds_id] for ds_id in contract.get("inputs", [])]
                outlets = [self.ctx.refs.dataset_urns[ds_id] for ds_id in contract.get("outputs", [])]

                self.ctx.client.entities.upsert(
                    self._flow_job_manager.build_datajob(
                        pipeline,
                        job,
                        inlets=inlets,
                        outlets=outlets,
                    )
                )
                print(f"upserted lineage contract for job {job['id']} (inputs={len(inlets)} outputs={len(outlets)})")
