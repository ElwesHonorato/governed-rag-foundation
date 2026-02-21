#!/usr/bin/env python3
"""Flow and job governance manager."""

from __future__ import annotations

from typing import Any

from datahub.metadata.urns import DataFlowUrn
from datahub.sdk import DataFlow, DataJob

from entities.shared.context import GovernanceContext


class FlowJobManager:
    """Apply flow and job template entities."""

    def __init__(self, ctx: GovernanceContext) -> None:
        """Store shared governance execution context."""

        self.ctx = ctx

    def apply(self, pipelines: list[dict[str, Any]]) -> None:
        """Upsert flows and jobs without lineage contract edges."""

        for pipeline in pipelines:
            for job in pipeline.get("jobs", []):
                self.ctx.client.entities.upsert(self.build_datajob(pipeline, job, inlets=[], outlets=[]))
                print(f"upserted job {job['id']}")

            flow_def = pipeline["flow"]
            flow = DataFlow(
                platform=flow_def["platform"],
                name=flow_def["name"],
                env=self.ctx.env_label,
                description=flow_def.get("description"),
                domain=self.ctx.refs.domain_urns[flow_def["domain"]],
                owners=[self.ctx.refs.group_urns[group_id] for group_id in flow_def.get("owners", [])],
            )
            self.ctx.client.entities.upsert(flow)
            print(f"upserted flow {flow_def['id']}")

    def build_datajob(self, pipeline: dict[str, Any], job: dict[str, Any], inlets: list[str], outlets: list[str]) -> Any:
        """Build one DataJob payload with optional inlets/outlets."""

        flow_def = pipeline["flow"]
        flow_urn = str(
            DataFlowUrn(
                orchestrator=flow_def["platform"],
                flow_id=flow_def["name"],
                cluster=self.ctx.env_label,
            )
        )

        return DataJob(
            name=job["name"],
            flow_urn=flow_urn,
            description=job.get("description"),
            custom_properties=job.get("custom_properties", {}),
            domain=self.ctx.refs.domain_urns[job["domain"]],
            owners=[self.ctx.refs.group_urns[group_id] for group_id in job.get("owners", [])],
            inlets=inlets,
            outlets=outlets,
        )
