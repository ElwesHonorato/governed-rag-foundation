#!/usr/bin/env python3
"""Flow and job governance manager."""

from __future__ import annotations

from typing import Any

from datahub.metadata.urns import DataFlowUrn
from datahub.sdk import DataFlow, DataJob

from entities.shared.context import FlowJobManagerContext


class FlowJobManager:
    """Apply flow and job template entities."""

    def __init__(self, governance_def_ctx: FlowJobManagerContext) -> None:
        """Store shared governance execution context."""

        self.governance_def_ctx = governance_def_ctx

    def apply(self, pipelines: list[dict[str, Any]]) -> None:
        """Upsert flows and jobs without lineage contract edges."""

        for pipeline in pipelines:
            for job in pipeline.get("jobs", []):
                self.governance_def_ctx.client.entities.upsert(self.build_datajob(pipeline, job, inlets=[], outlets=[]))
                print(f"upserted job {job['id']}")

            flow_def = pipeline["flow"]
            flow = DataFlow(
                platform=flow_def["platform"],
                name=flow_def["id"],
                env=self.governance_def_ctx.env,
                description=flow_def.get("description"),
                domain=self.governance_def_ctx.domain_urns[flow_def["domain"]],
                owners=[self.governance_def_ctx.group_urns[group_id] for group_id in flow_def.get("owners", [])],
            )
            self.governance_def_ctx.client.entities.upsert(flow)
            print(f"upserted flow {flow_def['id']}")

    def build_datajob(self, pipeline: dict[str, Any], job: dict[str, Any], inlets: list[str], outlets: list[str]) -> Any:
        """Build one DataJob payload with optional inlets/outlets."""

        flow_def = pipeline["flow"]
        flow_urn = str(
            DataFlowUrn(
                orchestrator=flow_def["platform"],
                flow_id=flow_def["id"],
                cluster=self.governance_def_ctx.env,
            )
        )

        return DataJob(
            name=job["id"],
            flow_urn=flow_urn,
            description=job.get("description"),
            custom_properties=job.get("custom_properties", {}),
            domain=self.governance_def_ctx.domain_urns[job["domain"]],
            owners=[self.governance_def_ctx.group_urns[group_id] for group_id in job.get("owners", [])],
            inlets=inlets,
            outlets=outlets,
        )
