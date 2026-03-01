#!/usr/bin/env python3
"""Governance apply orchestration."""

from __future__ import annotations

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
from entities.shared.ports import GovernanceCatalogWriterPort
from entities.shared.definitions import (
    DatasetDefinition,
    DomainDefinition,
    GroupDefinition,
    PipelineDefinition,
    TagDefinition,
    TermDefinition,
)
from state_loader import GovernanceState


class GovernanceApplier:
    """Apply governance definitions for one environment."""

    def __init__(
        self,
        *,
        env_name: str,
        state: GovernanceState,
        refs: ResolvedRefs,
        governance_writer: GovernanceCatalogWriterPort,
    ) -> None:
        """Store runtime state and port dependencies required for apply operations."""

        self.env = env_name
        self.state = state
        self.refs = refs
        self.governance_writer = governance_writer

    def _split_context_by_manager(self) -> ManagerContexts:
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

        return ManagerContexts(
            domain=DomainManagerContext(
                governance_writer=self.governance_writer,
                domain_urns=self.refs.domain_urns,
            ),
            group=GroupManagerContext(
                governance_writer=self.governance_writer,
                group_urns=self.refs.group_urns,
            ),
            taxonomy=TaxonomyManagerContext(
                governance_writer=self.governance_writer,
                term_urns=self.refs.term_urns,
            ),
            dataset=DatasetManagerContext(
                governance_writer=self.governance_writer,
                env=self.env,
                domain_urns=self.refs.domain_urns,
                group_urns=self.refs.group_urns,
                tag_urns=self.refs.tag_urns,
                term_urns=self.refs.term_urns,
            ),
            flow_job=FlowJobManagerContext(
                governance_writer=self.governance_writer,
                env=self.env,
                domain_urns=self.refs.domain_urns,
                group_urns=self.refs.group_urns,
            ),
            lineage=LineageContractManagerContext(
                governance_writer=self.governance_writer,
                env=self.env,
                domain_urns=self.refs.domain_urns,
                group_urns=self.refs.group_urns,
                dataset_urns=self.refs.dataset_urns,
            ),
        )

    def _apply_static(self, manager_contexts: ManagerContexts) -> None:
        """Apply static entities in dependency-safe order."""

        snapshot = self.state.governance_definitions_snapshot
        DomainManager(manager_contexts.domain).apply(
            [DomainDefinition.from_mapping(payload) for payload in snapshot.domains]
        )
        GroupManager(manager_contexts.group).apply(
            [GroupDefinition.from_mapping(payload) for payload in snapshot.groups]
        )
        TaxonomyManager(manager_contexts.taxonomy).apply(
            [TagDefinition.from_mapping(payload) for payload in snapshot.tags],
            [TermDefinition.from_mapping(payload) for payload in snapshot.terms],
        )

    def _apply_dynamic(self, manager_contexts: ManagerContexts) -> None:
        """Apply datasets, jobs, and lineage contracts."""

        snapshot = self.state.governance_definitions_snapshot
        pipelines = [PipelineDefinition.from_mapping(payload) for payload in snapshot.pipelines]
        DatasetManager(manager_contexts.dataset).apply(
            [DatasetDefinition.from_mapping(payload) for payload in snapshot.datasets]
        )
        FlowJobManager(manager_contexts.flow_job).apply(pipelines)
        LineageContractManager(manager_contexts.lineage).apply(pipelines)

    def apply(self) -> int:
        """Apply governance model."""

        manager_contexts = self._split_context_by_manager()
        self._apply_static(manager_contexts)
        self._apply_dynamic(manager_contexts)

        print("apply complete")
        return 0
