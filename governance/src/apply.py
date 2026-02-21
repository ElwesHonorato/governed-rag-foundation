#!/usr/bin/env python3
"""Apply governance definitions to DataHub in deterministic order."""

from __future__ import annotations

from datahub.ingestion.graph.client import DataHubGraph, DatahubClientConfig
from datahub.sdk import DataHubClient

from common import GovernanceStateLoader, parse_args
from entities import (
    DatasetManager,
    DomainManager,
    FlowJobManager,
    GovernanceContext,
    GroupManager,
    LineageContractManager,
    TaxonomyManager,
    resolve_refs,
)


def run_apply(env_name: str, static_only: bool = False) -> int:
    """Apply governance model to DataHub for one environment."""

    state = GovernanceStateLoader.load(env_name)
    env_label = env_name.upper()

    refs = resolve_refs(state.governance_definitions_snapshot, env_label)

    client = DataHubClient(server=state.env_settings.gms_server, token=state.env_settings.token)

    with DataHubGraph(
        DatahubClientConfig(server=state.env_settings.gms_server, token=state.env_settings.token)
    ) as graph:
        ctx = GovernanceContext(env_label=env_label, client=client, graph=graph, refs=refs)

        # Order matters for dependencies.
        DomainManager(ctx).apply(state.governance_definitions_snapshot.domains)
        GroupManager(ctx).apply(state.governance_definitions_snapshot.groups)
        TaxonomyManager(ctx).apply(state.governance_definitions_snapshot.tags, state.governance_definitions_snapshot.terms)

        if static_only:
            print("bootstrap complete")
            return 0

        DatasetManager(ctx).apply(state.governance_definitions_snapshot.datasets)
        FlowJobManager(ctx).apply(state.governance_definitions_snapshot.pipelines)
        LineageContractManager(ctx).apply(state.governance_definitions_snapshot.pipelines)

    print("apply complete")
    return 0


def main() -> int:
    """CLI entrypoint for full governance apply."""

    args = parse_args()
    return run_apply(args.env, static_only=False)


if __name__ == "__main__":
    raise SystemExit(main())
