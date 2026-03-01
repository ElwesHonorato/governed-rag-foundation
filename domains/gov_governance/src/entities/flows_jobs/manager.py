#!/usr/bin/env python3
"""Flow and job governance manager."""

from __future__ import annotations

from entities.shared.context import FlowJobManagerContext
from entities.shared.definitions import JobDefinition, PipelineDefinition
from entities.shared.ports import GovernanceCatalogWriterPort


class FlowJobManager:
    """Apply flow and job template entities."""

    def __init__(self, governance_def_ctx: FlowJobManagerContext) -> None:
        """Store shared governance execution context."""

        self.governance_def_ctx = governance_def_ctx
        self._governance_writer: GovernanceCatalogWriterPort = governance_def_ctx.governance_writer

    def apply(self, pipelines: list[PipelineDefinition]) -> None:
        """Upsert flows and jobs without lineage contract edges."""

        for pipeline in pipelines:
            for job in pipeline.jobs:
                self._upsert_job(pipeline, job, inlets=[], outlets=[])
                print(f"upserted job {job.id}")

            flow_def = pipeline.flow
            self._governance_writer.upsert_flow(
                platform=flow_def.platform,
                flow_id=flow_def.id,
                env=self.governance_def_ctx.env,
                description=flow_def.description,
                domain=self.governance_def_ctx.domain_urns[flow_def.domain],
                owners=[self.governance_def_ctx.group_urns[group_id] for group_id in flow_def.owners],
            )
            print(f"upserted flow {flow_def.id}")

    def _upsert_job(
        self,
        pipeline: PipelineDefinition,
        job: JobDefinition,
        inlets: list[str],
        outlets: list[str],
    ) -> None:
        """Upsert one DataJob payload with optional inlets/outlets."""
        flow_def = pipeline.flow
        self._governance_writer.upsert_job(
            flow_platform=flow_def.platform,
            flow_id=flow_def.id,
            env=self.governance_def_ctx.env,
            job_id=job.id,
            description=job.description,
            custom_properties=job.custom_properties,
            domain=self.governance_def_ctx.domain_urns[job.domain],
            owners=[self.governance_def_ctx.group_urns[group_id] for group_id in job.owners],
            inlets=inlets,
            outlets=outlets,
        )
