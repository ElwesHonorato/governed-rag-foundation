#!/usr/bin/env python3
"""CLI entrypoint for governance apply."""

from __future__ import annotations

from datahub.ingestion.graph.client import DataHubGraph, DatahubClientConfig
from datahub.sdk import DataHubClient

from infrastructure.datahub import DataHubGovernanceCatalogWriter
from orchestration.governance_applier import GovernanceApplier
from pipeline_common.helpers.config import _required_env
from pipeline_common.settings import SettingsProvider, SettingsRequest
from state_loader import GovernanceStateLoader


def main() -> int:
    """CLI entrypoint for governance apply."""

    settings = SettingsProvider(SettingsRequest(datahub=True)).bundle
    datahub_settings = settings.datahub
    env_name = _required_env("DATAHUB_ENV")
    state = GovernanceStateLoader(env_name).state
    client = DataHubClient(
        server=datahub_settings.server,
        token=datahub_settings.token,
    )
    graph_config = DatahubClientConfig(
        server=datahub_settings.server,
        token=datahub_settings.token,
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
