#!/usr/bin/env python3
"""Domain governance manager."""

from __future__ import annotations

from typing import Any

from entities.domain.ports import DomainCatalogWriter
from entities.shared.context import DomainManagerContext


class DomainManager:
    """Apply domain definitions to DataHub."""

    def __init__(self, governance_def_ctx: DomainManagerContext) -> None:
        """Store shared governance execution context."""

        self.governance_def_ctx = governance_def_ctx
        self._domain_writer: DomainCatalogWriter = governance_def_ctx.domain_writer

    def apply(self, domains: list[dict[str, Any]]) -> None:
        """Upsert all domain entities and parent relationships."""

        for domain in domains:
            parent_urn = self.governance_def_ctx.domain_urns.get(domain.get("parent", ""))
            self._domain_writer.upsert_domain(
                entity_urn=self.governance_def_ctx.domain_urns[domain["id"]],
                name=domain["name"],
                description=domain.get("description"),
                parent_domain_urn=parent_urn,
            )
            print(f"upserted domain {domain['id']}")
