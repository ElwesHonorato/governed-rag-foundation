#!/usr/bin/env python3
"""Apply governance definitions to DataHub in deterministic order."""

from __future__ import annotations

from datahub.ingestion.graph.client import DataHubGraph, DatahubClientConfig
from datahub.sdk import DataHubClient

from _common import load_env_config, load_model, parse_args, token_from_env
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

    env_cfg = load_env_config(env_name)
    model = load_model()
    env_label = env_name.upper()

    token = token_from_env(env_cfg.token_env)
    refs = resolve_refs(model, env_label)

    client = DataHubClient(server=env_cfg.gms_server, token=token)

    with DataHubGraph(DatahubClientConfig(server=env_cfg.gms_server, token=token)) as graph:
        ctx = GovernanceContext(env_label=env_label, client=client, graph=graph, refs=refs)

        # Order matters for dependencies.
        DomainManager(ctx).apply(model.domains)
        GroupManager(ctx).apply(model.groups)
        TaxonomyManager(ctx).apply(model.tags, model.terms)

        if static_only:
            print("bootstrap complete")
            return 0

        DatasetManager(ctx).apply(model.datasets)
        FlowJobManager(ctx).apply(model.pipelines)
        LineageContractManager(ctx).apply(model.pipelines)

    print("apply complete")
    return 0


def main() -> int:
    """CLI entrypoint for full governance apply."""

    args = parse_args()
    return run_apply(args.env, static_only=False)


if __name__ == "__main__":
    raise SystemExit(main())
