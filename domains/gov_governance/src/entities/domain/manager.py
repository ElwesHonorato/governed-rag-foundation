#!/usr/bin/env python3
"""Domain governance manager."""

from __future__ import annotations

import logging

from entities.shared.context import DomainManagerContext
from entities.shared.definitions import DomainDefinition
from entities.shared.ports import GovernanceCatalogWriterPort

logger = logging.getLogger(__name__)


class DomainManager:
    """Apply domain definitions to DataHub."""

    def __init__(self, governance_def_ctx: DomainManagerContext) -> None:
        """Store shared governance execution context."""

        self.governance_def_ctx = governance_def_ctx
        self._governance_writer: GovernanceCatalogWriterPort = governance_def_ctx.governance_writer

    def apply(self, domains: list[DomainDefinition]) -> None:
        """Upsert all domain entities and parent relationships."""

        for domain in domains:
            parent_urn = self.governance_def_ctx.domain_urns.get(domain.parent or "")
            self._governance_writer.upsert_domain(
                entity_urn=self.governance_def_ctx.domain_urns[domain.id],
                name=domain.name,
                description=domain.description,
                parent_domain_urn=parent_urn,
            )
            logger.info("upserted domain %s", domain.id)
