#!/usr/bin/env python3
"""Apply governance definitions to DataHub in deterministic order."""

from __future__ import annotations

from datahub.metadata.urns import CorpGroupUrn, DatasetUrn, DomainUrn, GlossaryTermUrn, TagUrn
from datahub.ingestion.graph.client import DataHubGraph, DatahubClientConfig
from datahub.sdk import DataHubClient

from common import GovernanceStateLoader, resolve_env
from entities import (
    DatasetManager,
    DomainManager,
    FlowJobManager,
    GovernanceContext,
    GroupManager,
    LineageContractManager,
    ResolvedRefs,
    TaxonomyManager,
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

    def _apply_static(self, governance_def_ctx: GovernanceContext) -> None:
        """Apply static entities in dependency-safe order."""

        DomainManager(governance_def_ctx).apply(self.state.governance_definitions_snapshot.domains)
        GroupManager(governance_def_ctx).apply(self.state.governance_definitions_snapshot.groups)
        TaxonomyManager(governance_def_ctx).apply(
            self.state.governance_definitions_snapshot.tags,
            self.state.governance_definitions_snapshot.terms,
        )

    def _apply_dynamic(self, governance_def_ctx: GovernanceContext) -> None:
        """Apply datasets, jobs, and lineage contracts."""

        DatasetManager(governance_def_ctx).apply(self.state.governance_definitions_snapshot.datasets)
        FlowJobManager(governance_def_ctx).apply(self.state.governance_definitions_snapshot.pipelines)
        LineageContractManager(governance_def_ctx).apply(self.state.governance_definitions_snapshot.pipelines)

    def apply(self) -> int:
        """Apply governance model."""

        with DataHubGraph(self.graph_config) as graph:
            governance_def_ctx = GovernanceContext(
                env=self.env,
                client=self.client,
                graph=graph,
                refs=self.refs,
            )
            self._apply_static(governance_def_ctx)
            self._apply_dynamic(governance_def_ctx)

        print("apply complete")
        return 0

def main() -> int:
    """CLI entrypoint for governance apply."""

    return GovernanceApplier(resolve_env()).apply()


if __name__ == "__main__":
    raise SystemExit(main())
