#!/usr/bin/env python3
"""Governance apply orchestration."""

from __future__ import annotations

from datahub.ingestion.graph.client import DataHubGraph, DatahubClientConfig
from datahub.metadata.urns import CorpGroupUrn, DatasetUrn, DomainUrn, GlossaryTermUrn, TagUrn
from datahub.sdk import DataHubClient

from infrastructure.datahub import DataHubGovernanceCatalogWriter
from state_loader import GovernanceStateLoader
from entities import (
    DatasetManager,
    DatasetManagerContext,
    DomainManager,
    DomainManagerContext,
    FlowJobManager,
    FlowJobManagerContext,
    GroupManager,
    GroupManagerContext,
    LineageContractManager,
    LineageContractManagerContext,
    ManagerContexts,
    ResolvedRefs,
    TaxonomyManager,
    TaxonomyManagerContext,
)


class GovernanceApplier:
    """Apply governance definitions for one environment."""

    def __init__(self, env_name: str) -> None:
        """Load environment state and initialize client/config for apply operations."""

        self.env = env_name
        self.state = GovernanceStateLoader.load(env_name)
        self.refs = self._resolve_refs()
        self.client = DataHubClient(
            server=self.state.env_settings.gms_server,
            token=self.state.env_settings.token,
        )
        self.graph_config = DatahubClientConfig(
            server=self.state.env_settings.gms_server,
            token=self.state.env_settings.token,
        )

    def _resolve_refs(self) -> ResolvedRefs:
        """Resolve commonly used URN mappings for this applier instance."""

        snapshot = self.state.governance_definitions_snapshot
        return ResolvedRefs(
            domain_urns={d["id"]: str(DomainUrn(d["id"])) for d in snapshot.domains},
            group_urns={g["id"]: str(CorpGroupUrn(g["id"])) for g in snapshot.groups},
            tag_urns={t["id"]: str(TagUrn(t["name"])) for t in snapshot.tags},
            term_urns={t["id"]: str(GlossaryTermUrn(t["id"])) for t in snapshot.terms},
            dataset_urns={
                d["id"]: str(DatasetUrn(platform=d["platform"], name=d["name"], env=self.env))
                for d in snapshot.datasets
            },
        )

    def _split_context_by_manager(self, graph) -> ManagerContexts:
        """Split runtime state into manager-specific contexts.

        Example (dataset path):
        - dataset row:
          {
            "domain": "rag-platform",
            "owners": ["search-platform"],
            "tags": ["internal"],
            "terms": ["embedding"]
          }
        - context maps produced here:
          domain_urns["rag-platform"] -> "urn:li:domain:rag-platform"
          group_urns["search-platform"] -> "urn:li:corpGroup:search-platform"
          tag_urns["internal"] -> "urn:li:tag:internal"
          term_urns["embedding"] -> "urn:li:glossaryTerm:embedding"
        - DatasetManager then resolves each field by key from the corresponding map.
        """

        governance_writer = DataHubGovernanceCatalogWriter(
            graph=graph,
            client=self.client,
        )
        return ManagerContexts(
            domain=DomainManagerContext(
                governance_writer=governance_writer,
                domain_urns=self.refs.domain_urns,
            ),
            group=GroupManagerContext(
                governance_writer=governance_writer,
                group_urns=self.refs.group_urns,
            ),
            taxonomy=TaxonomyManagerContext(
                governance_writer=governance_writer,
                term_urns=self.refs.term_urns,
            ),
            dataset=DatasetManagerContext(
                governance_writer=governance_writer,
                env=self.env,
                domain_urns=self.refs.domain_urns,
                group_urns=self.refs.group_urns,
                tag_urns=self.refs.tag_urns,
                term_urns=self.refs.term_urns,
            ),
            flow_job=FlowJobManagerContext(
                governance_writer=governance_writer,
                env=self.env,
                domain_urns=self.refs.domain_urns,
                group_urns=self.refs.group_urns,
            ),
            lineage=LineageContractManagerContext(
                governance_writer=governance_writer,
                env=self.env,
                domain_urns=self.refs.domain_urns,
                group_urns=self.refs.group_urns,
                dataset_urns=self.refs.dataset_urns,
            ),
        )

    def _apply_static(self, manager_contexts: ManagerContexts) -> None:
        """Apply static entities in dependency-safe order."""

        DomainManager(manager_contexts.domain).apply(self.state.governance_definitions_snapshot.domains)
        GroupManager(manager_contexts.group).apply(self.state.governance_definitions_snapshot.groups)
        TaxonomyManager(manager_contexts.taxonomy).apply(
            self.state.governance_definitions_snapshot.tags,
            self.state.governance_definitions_snapshot.terms,
        )

    def _apply_dynamic(self, manager_contexts: ManagerContexts) -> None:
        """Apply datasets, jobs, and lineage contracts."""

        DatasetManager(manager_contexts.dataset).apply(self.state.governance_definitions_snapshot.datasets)
        FlowJobManager(manager_contexts.flow_job).apply(self.state.governance_definitions_snapshot.pipelines)
        LineageContractManager(manager_contexts.lineage).apply(
            self.state.governance_definitions_snapshot.pipelines
        )

    def apply(self) -> int:
        """Apply governance model."""

        with DataHubGraph(self.graph_config) as graph:
            manager_contexts = self._split_context_by_manager(graph)
            self._apply_static(manager_contexts)
            self._apply_dynamic(manager_contexts)

        print("apply complete")
        return 0
