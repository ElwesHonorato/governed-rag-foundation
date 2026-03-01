#!/usr/bin/env python3
"""CLI entrypoint for governance apply."""

from __future__ import annotations

from datahub.ingestion.graph.client import DataHubGraph, DatahubClientConfig
from datahub.sdk import DataHubClient

from infrastructure.datahub import DataHubGovernanceCatalogWriter
from orchestration.governance_applier import GovernanceApplier
from state_loader import GovernanceStateLoader, resolve_env


def main() -> int:
    """CLI entrypoint for governance apply."""

    env_name = resolve_env()
    state = GovernanceStateLoader.load(env_name)
    client = DataHubClient(
        server=state.env_settings.gms_server,
        token=state.env_settings.token,
    )
    graph_config = DatahubClientConfig(
        server=state.env_settings.gms_server,
        token=state.env_settings.token,
    )
    with DataHubGraph(graph_config) as graph:
        governance_writer = DataHubGovernanceCatalogWriter(graph=graph, client=client)
        return GovernanceApplier(
            env_name=env_name,
            state=state,
            governance_writer=governance_writer,
        ).apply()


if __name__ == "__main__":
    raise SystemExit(main())
