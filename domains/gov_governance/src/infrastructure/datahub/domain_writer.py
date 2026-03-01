#!/usr/bin/env python3
"""DataHub adapter for domain governance writes."""

from __future__ import annotations

from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import ChangeTypeClass, DomainPropertiesClass

from entities.domain.ports import DomainCatalogWriter


class DataHubDomainWriter(DomainCatalogWriter):
    """Write governance domains to DataHub via MCP upserts."""

    def __init__(self, graph) -> None:
        self._graph = graph

    def upsert_domain(
        self,
        *,
        entity_urn: str,
        name: str,
        description: str | None,
        parent_domain_urn: str | None,
    ) -> None:
        aspect = DomainPropertiesClass(
            name=name,
            description=description,
            parentDomain=parent_domain_urn,
        )
        self._graph.emit(
            MetadataChangeProposalWrapper(
                entityUrn=entity_urn,
                entityType="domain",
                aspectName="domainProperties",
                aspect=aspect,
                changeType=ChangeTypeClass.UPSERT,
            )
        )
