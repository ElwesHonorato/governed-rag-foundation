#!/usr/bin/env python3
"""Domain governance manager."""

from __future__ import annotations

from typing import Any

from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import ChangeTypeClass, DomainPropertiesClass

from entities.shared.context import DomainManagerContext


class DomainManager:
    """Apply domain definitions to DataHub."""

    def __init__(self, governance_def_ctx: DomainManagerContext) -> None:
        """Store shared governance execution context."""

        self.governance_def_ctx = governance_def_ctx

    def apply(self, domains: list[dict[str, Any]]) -> None:
        """Upsert all domain entities and parent relationships."""

        for domain in domains:
            parent_urn = self.governance_def_ctx.refs.domain_urns.get(domain.get("parent", ""))
            aspect = DomainPropertiesClass(
                name=domain["name"],
                description=domain.get("description"),
                parentDomain=parent_urn,
            )
            self.governance_def_ctx.graph.emit(
                MetadataChangeProposalWrapper(
                    entityUrn=self.governance_def_ctx.refs.domain_urns[domain["id"]],
                    entityType="domain",
                    aspectName="domainProperties",
                    aspect=aspect,
                    changeType=ChangeTypeClass.UPSERT,
                )
            )
            print(f"upserted domain {domain['id']}")
