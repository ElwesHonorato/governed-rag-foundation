#!/usr/bin/env python3
"""Lineage contract governance manager."""

from __future__ import annotations

import logging

from gov_governance.entities.shared.context import LineageContractManagerContext
from gov_governance.entities.shared.definitions import PipelineDefinition
from gov_governance.entities.shared.ports import GovernanceCatalogWriterPort

logger = logging.getLogger(__name__)


class LineageContractManager:
    """Apply lineage contract edges to existing jobs.

    Design note:
    This is phase two of the explicit two-phase job upsert strategy.
    Jobs are first created/updated in ``FlowJobManager``, then re-upserted here
    with inlets/outlets from lineage contracts.
    """

    def __init__(self, governance_def_ctx: LineageContractManagerContext) -> None:
        """Store lineage context and governance catalog writer."""

        self.governance_def_ctx = governance_def_ctx
        self._governance_writer: GovernanceCatalogWriterPort = governance_def_ctx.governance_writer

    def apply(self, pipelines: list[PipelineDefinition]) -> None:
        """Upsert DataJob inlets/outlets for each lineage contract entry."""

        for pipeline in pipelines:
            contracts = {contract.job: contract for contract in pipeline.lineage_contract}
            for job in pipeline.jobs:
                contract = contracts.get(job.id)
                if contract is None:
                    continue

                inlets = [self.governance_def_ctx.dataset_urns[ds_id] for ds_id in contract.inputs]
                outlets = [self.governance_def_ctx.dataset_urns[ds_id] for ds_id in contract.outputs]

                flow_def = pipeline.flow
                self._governance_writer.upsert_job(
                    flow_platform=flow_def.platform,
                    flow_id=flow_def.id,
                    env=self.governance_def_ctx.env,
                    job_id=job.id,
                    description=job.description,
                    custom_properties=job.custom_properties,
                    domain=self.governance_def_ctx.domain_urns[job.domain],
                    owners=[
                        self.governance_def_ctx.group_urns[group_id]
                        for group_id in job.owners
                    ],
                    inlets=inlets,
                    outlets=outlets,
                )
                logger.info(
                    "upserted lineage contract for job %s (inputs=%d outputs=%d)",
                    job.id,
                    len(inlets),
                    len(outlets),
                )
