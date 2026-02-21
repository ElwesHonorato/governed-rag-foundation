#!/usr/bin/env python3
"""Domain governance manager."""

from __future__ import annotations

from typing import Any

from entities.shared.context import GovernanceContext


class DomainManager:
    """Apply domain definitions to DataHub."""

    def __init__(self, ctx: GovernanceContext) -> None:
        """Store shared governance execution context."""

        self.ctx = ctx

    def apply(self, domains: list[dict[str, Any]]) -> None:
        """Upsert all domain entities and parent relationships."""

        from datahub.emitter.mcp import MetadataChangeProposalWrapper
        from datahub.metadata.schema_classes import ChangeTypeClass, DomainPropertiesClass

        for domain in domains:
            parent_urn = self.ctx.refs.domain_urns.get(domain.get("parent", ""))
            aspect = DomainPropertiesClass(
                name=domain["name"],
                description=domain.get("description"),
                parentDomain=parent_urn,
            )
            self.ctx.graph.emit(
                MetadataChangeProposalWrapper(
                    entityUrn=self.ctx.refs.domain_urns[domain["id"]],
                    entityType="domain",
                    aspectName="domainProperties",
                    aspect=aspect,
                    changeType=ChangeTypeClass.UPSERT,
                )
            )
            print(f"upserted domain {domain['id']}")
