#!/usr/bin/env python3
"""Generate a read-only governance apply plan for DataHub entities."""

from __future__ import annotations

import argparse
import os

from _common import ALLOWED_ENVS, load_env_config, load_model, token_from_env


def main() -> int:
    """Build and print an apply plan for the selected environment."""

    env_from_var = os.getenv("ENV", "dev").strip().lower()
    if env_from_var not in ALLOWED_ENVS:
        raise SystemExit(f"Invalid ENV='{os.getenv('ENV')}'. Allowed values: {', '.join(ALLOWED_ENVS)}")

    parser = argparse.ArgumentParser()
    parser.add_argument("--env", choices=list(ALLOWED_ENVS), default=env_from_var)
    parser.add_argument("--offline", action="store_true", help="Skip DataHub existence checks")
    args = parser.parse_args()
    env_cfg = load_env_config(args.env)
    model = load_model()

    from datahub.ingestion.graph.client import DataHubGraph, DatahubClientConfig
    from datahub.metadata.urns import CorpGroupUrn, DataFlowUrn, DataJobUrn, DatasetUrn, DomainUrn, GlossaryTermUrn, TagUrn

    def exists(graph: DataHubGraph | None, urn: str) -> bool | None:
        """Check whether a URN exists, returning `None` on unknown/error."""

        if graph is None:
            return None
        try:
            return bool(graph.exists(urn))
        except Exception:
            return None

    token = token_from_env(env_cfg.token_env)
    graph: DataHubGraph | None = None

    if not args.offline:
        try:
            graph = DataHubGraph(DatahubClientConfig(server=env_cfg.gms_server, token=token, timeout_sec=5))
        except Exception as exc:
            print(f"WARN: could not connect to DataHub for existence checks: {exc}")

    def action_for(urn: str) -> str:
        """Convert existence state into a human-readable plan action."""

        result = exists(graph, urn)
        if result is None:
            return "upsert"
        return "update" if result else "create"

    print(f"Plan for env={env_cfg.env} server={env_cfg.gms_server}")

    print("\nDomains")
    for domain in model.domains:
        urn = str(DomainUrn(domain["id"]))
        print(f"- would {action_for(urn)} domain {domain['id']} ({urn})")

    print("\nGroups")
    for group in model.groups:
        urn = str(CorpGroupUrn(group["id"]))
        print(f"- would {action_for(urn)} group {group['id']} ({urn})")

    print("\nTags")
    for tag in model.tags:
        urn = str(TagUrn(tag["name"]))
        print(f"- would {action_for(urn)} tag {tag['name']} ({urn})")

    print("\nGlossary Terms")
    for term in model.terms:
        urn = str(GlossaryTermUrn(term["id"]))
        print(f"- would {action_for(urn)} term {term['id']} ({urn})")

    print("\nDatasets")
    for dataset in model.datasets:
        urn = str(DatasetUrn(platform=dataset["platform"], name=dataset["name"], env=env_cfg.env))
        print(f"- would {action_for(urn)} dataset {dataset['id']} ({urn})")

    print("\nFlows + Jobs + Lineage Contract")
    for pipeline in model.pipelines:
        flow = pipeline["flow"]
        flow_urn = DataFlowUrn(orchestrator=flow["platform"], flow_id=flow["name"], cluster=env_cfg.env)
        print(f"- would {action_for(str(flow_urn))} flow {flow['id']} ({flow_urn})")

        contracts = {c["job"]: c for c in pipeline.get("lineage_contract", [])}
        for job in pipeline.get("jobs", []):
            job_urn = DataJobUrn(flow_urn, job["name"])
            print(f"- would {action_for(str(job_urn))} job {job['id']} ({job_urn})")

            contract = contracts.get(job["id"])
            if contract:
                n_in = len(contract.get("inputs", []))
                n_out = len(contract.get("outputs", []))
                print(f"- would set lineage edges for job {job['id']} ({n_in} input, {n_out} output)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
