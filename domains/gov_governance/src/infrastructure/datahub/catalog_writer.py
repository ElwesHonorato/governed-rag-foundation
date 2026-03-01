#!/usr/bin/env python3
"""DataHub adapter implementing governance catalog writer port."""

from __future__ import annotations

from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import (
    ChangeTypeClass,
    CorpGroupInfoClass,
    DomainPropertiesClass,
    GlossaryTermInfoClass,
)
from datahub.metadata.urns import DataFlowUrn
from datahub.sdk import DataFlow, DataJob, Dataset, Tag

from entities.shared.ports import GovernanceCatalogWriterPort


class DataHubGovernanceCatalogWriter(GovernanceCatalogWriterPort):
    """Write governance entities to DataHub using SDK/MCP operations."""

    def __init__(self, *, graph, client) -> None:
        self._graph = graph
        self._client = client

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

    def upsert_group(
        self,
        *,
        entity_urn: str,
        display_name: str | None,
        description: str | None,
        admins: list[str],
        members: list[str],
        groups: list[str],
    ) -> None:
        aspect = CorpGroupInfoClass(
            displayName=display_name,
            description=description,
            admins=admins,
            members=members,
            groups=groups,
        )
        self._graph.emit(
            MetadataChangeProposalWrapper(
                entityUrn=entity_urn,
                entityType="corpGroup",
                aspectName="corpGroupInfo",
                aspect=aspect,
                changeType=ChangeTypeClass.UPSERT,
            )
        )

    def upsert_tag(
        self,
        *,
        name: str,
        display_name: str | None,
        description: str | None,
    ) -> None:
        self._client.entities.upsert(
            Tag(
                name=name,
                display_name=display_name,
                description=description,
            )
        )

    def upsert_glossary_term(
        self,
        *,
        entity_urn: str,
        term_id: str,
        name: str,
        definition: str | None,
    ) -> None:
        aspect = GlossaryTermInfoClass(
            id=term_id,
            name=name,
            definition=definition,
            termSource="INTERNAL",
        )
        self._graph.emit(
            MetadataChangeProposalWrapper(
                entityUrn=entity_urn,
                entityType="glossaryTerm",
                aspectName="glossaryTermInfo",
                aspect=aspect,
                changeType=ChangeTypeClass.UPSERT,
            )
        )

    def upsert_dataset(
        self,
        *,
        platform: str,
        name: str,
        env: str,
        description: str | None,
        domain: str,
        owners: list[str],
        tags: list[str],
        terms: list[str],
    ) -> None:
        self._client.entities.upsert(
            Dataset(
                platform=platform,
                name=name,
                env=env,
                description=description,
                domain=domain,
                owners=owners,
                tags=tags,
                terms=terms,
            )
        )

    def upsert_flow(
        self,
        *,
        platform: str,
        flow_id: str,
        env: str,
        description: str | None,
        domain: str,
        owners: list[str],
    ) -> None:
        self._client.entities.upsert(
            DataFlow(
                platform=platform,
                name=flow_id,
                env=env,
                description=description,
                domain=domain,
                owners=owners,
            )
        )

    def upsert_job(
        self,
        *,
        flow_platform: str,
        flow_id: str,
        env: str,
        job_id: str,
        description: str | None,
        custom_properties: dict[str, str],
        domain: str,
        owners: list[str],
        inlets: list[str],
        outlets: list[str],
    ) -> None:
        flow_urn = str(
            DataFlowUrn(
                orchestrator=flow_platform,
                flow_id=flow_id,
                cluster=env,
            )
        )
        self._client.entities.upsert(
            DataJob(
                name=job_id,
                flow_urn=flow_urn,
                description=description,
                custom_properties=custom_properties,
                domain=domain,
                owners=owners,
                inlets=inlets,
                outlets=outlets,
            )
        )
