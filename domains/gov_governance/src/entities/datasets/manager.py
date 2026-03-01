#!/usr/bin/env python3
"""Dataset governance manager."""

from __future__ import annotations

import logging

from entities.shared.context import DatasetManagerContext
from entities.shared.definitions import DatasetDefinition
from entities.shared.ports import GovernanceCatalogWriterPort

logger = logging.getLogger(__name__)


class DatasetManager:
    """Apply dataset definitions and metadata assignments."""

    def __init__(self, governance_def_ctx: DatasetManagerContext) -> None:
        """Store shared governance execution context."""

        self.governance_def_ctx = governance_def_ctx
        self._governance_writer: GovernanceCatalogWriterPort = governance_def_ctx.governance_writer

    def apply(self, datasets: list[DatasetDefinition]) -> None:
        """Upsert all datasets with domain, owners, tags, and terms."""

        for dataset in datasets:
            self._governance_writer.upsert_dataset(
                platform=dataset.platform,
                name=dataset.name,
                env=self.governance_def_ctx.env,
                description=dataset.description,
                domain=self.governance_def_ctx.domain_urns[dataset.domain],
                owners=[self.governance_def_ctx.group_urns[group_id] for group_id in dataset.owners],
                tags=[self.governance_def_ctx.tag_urns[tag_id] for tag_id in dataset.tags],
                terms=[self.governance_def_ctx.term_urns[term_id] for term_id in dataset.terms],
            )
            logger.info("upserted dataset %s", dataset.id)
