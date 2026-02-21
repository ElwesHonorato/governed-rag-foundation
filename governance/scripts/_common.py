#!/usr/bin/env python3
"""Shared config/model loading utilities for governance scripts."""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml


ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
ALLOWED_ENVS = ("dev", "prod")


class DefinitionType(StrEnum):
    """Supported governance definition file types."""

    DOMAINS = "domains"
    GROUPS = "groups"
    TAGS = "tags"
    TERMS = "terms"
    DATASETS = "datasets"
    FLOW = "flow"
    JOBS = "jobs"
    LINEAGE_CONTRACT = "lineage_contract"

    @property
    def standalone_key(self) -> str | None:
        """Return the top-level list key for standalone-list definitions."""

        if self in (
            DefinitionType.DOMAINS,
            DefinitionType.GROUPS,
            DefinitionType.TAGS,
            DefinitionType.TERMS,
            DefinitionType.DATASETS,
        ):
            return self.value
        return None

    @classmethod
    def standalone_types(cls) -> tuple["DefinitionType", ...]:
        """Return definition types that are aggregated as standalone list payloads."""

        return tuple(definition_type for definition_type in cls if definition_type.standalone_key is not None)


@dataclass(frozen=True)
class EnvironmentConfig:
    """Runtime config for a target DataHub environment."""

    gms_server: str
    token_env: str
    env: str


@dataclass(frozen=True)
class GovernanceModel:
    """In-memory representation of governance YAML definitions."""

    domains: list[dict[str, Any]]
    groups: list[dict[str, Any]]
    tags: list[dict[str, Any]]
    terms: list[dict[str, Any]]
    datasets: list[dict[str, Any]]
    pipelines: list[dict[str, Any]]


class GovernanceYamlLoader:
    """Encapsulate governance YAML discovery, classification, and loading.

    Example object output from ``load_model()``::
        GovernanceModel(
            domains=[{"id": "rag-platform", "name": "RAG Platform"}],
            groups=[{"id": "search-platform", "name": "Search Platform"}],
            tags=[{"id": "pii"}],
            terms=[{"id": "customer_id"}],
            datasets=[{"id": "s3://rag-data:02_raw/pg100-images.html"}],
            pipelines=[{
                "flow": {"id": "governed-rag", "name": "governed-rag", "platform": "custom"},
                "jobs": [{"id": "worker_chunk_text", "name": "worker_chunk_text"}],
                "lineage_contract": [{"job": "worker_chunk_text", "inputs": [], "outputs": []}],
            }],
        )
    """

    def __init__(self, definitions_root: Path, definition_type: DefinitionType | None = None) -> None:
        """Initialize loader with a definitions root and optional type filter."""

        self.definitions_root = definitions_root
        self.definition_type = definition_type
        self.standalone_discovered_definitions: dict[DefinitionType, dict[Path, dict[str, Any]]] = {}
        self.relational_discovered_definitions: dict[DefinitionType, dict[Path, dict[str, Any]]] = {}

    def load_model(self) -> GovernanceModel:
        """Load all governance definitions into a typed model."""

        self._discover_definition_files()
        list_payloads = self._build_standalone_payloads()

        return GovernanceModel(
            domains=list_payloads.get(DefinitionType.DOMAINS, []),
            groups=list_payloads.get(DefinitionType.GROUPS, []),
            tags=list_payloads.get(DefinitionType.TAGS, []),
            terms=list_payloads.get(DefinitionType.TERMS, []),
            datasets=list_payloads.get(DefinitionType.DATASETS, []),
            pipelines=self._build_pipelines(),
        )

    def _discover_definition_files(self) -> None:
        """Discover YAML files and partition by standalone vs relational definitions.

        Example dictionary outputs::
            self.standalone_discovered_definitions = {
                DefinitionType.DATASETS: {
                    Path("governance/definitions/400_datasets/420_s3.yaml"): {"datasets": [...]}
                }
            }
            self.relational_discovered_definitions = {
                DefinitionType.FLOW: {
                    Path("governance/definitions/500_flow/500_governed-rag.yaml"): {"flow": {...}}
                },
                DefinitionType.JOBS: {
                    Path("governance/definitions/600_jobs/600_governed-rag.yaml"): {"flow_id": "governed-rag", "jobs": [...]}
                },
            }
        """

        self.standalone_discovered_definitions = {}
        self.relational_discovered_definitions = {}

        for path in sorted(self.definitions_root.rglob("*.yaml")):
            data = self._read_yaml(path)
            definition_type = self._resolve_definition_type(path, data)
            if self.definition_type is not None and definition_type != self.definition_type:
                continue
            if definition_type.standalone_key is None:
                self.relational_discovered_definitions.setdefault(definition_type, {})[path] = data
            else:
                self.standalone_discovered_definitions.setdefault(definition_type, {})[path] = data

    def _build_standalone_payloads(self) -> dict[DefinitionType, list[dict[str, Any]]]:
        """Build aggregated payloads for standalone definition types.

        Example dictionary output::
            {
                DefinitionType.DOMAINS: [{"id": "rag-platform", "name": "RAG Platform"}],
                DefinitionType.DATASETS: [{"id": "s3://rag-data:02_raw/pg100-images.html"}],
            }
        """

        return {
            definition_type: self._items_for_standalone_type(definition_type)
            for definition_type in self.standalone_discovered_definitions
        }

    def _items_for_standalone_type(self, definition_type: DefinitionType) -> list[dict[str, Any]]:
        """Aggregate list items for one standalone definition type."""

        key = definition_type.standalone_key
        standalone_entities_definitions: list[dict[str, Any]] = []
        standalone_type_payloads = self.standalone_discovered_definitions.get(definition_type, {})
        for payload in standalone_type_payloads.values():
            standalone_entities_definitions.extend(payload.get(key, []))
        return standalone_entities_definitions

    def _build_pipelines(self) -> list[dict[str, Any]]:
        """Build canonical pipeline list payloads from flow, jobs, and lineage files.

        Example list output::
            [{
                "flow": {"id": "governed-rag", "name": "governed-rag", "platform": "custom"},
                "jobs": [{"id": "worker_chunk_text", "name": "worker_chunk_text"}],
                "lineage_contract": [{"job": "worker_chunk_text", "inputs": [], "outputs": []}],
            }]
        """

        flow_by_id: dict[str, dict[str, Any]] = {}
        for path, data in self.relational_discovered_definitions.get(DefinitionType.FLOW, {}).items():
            raw_flows = data.get("flows", data.get("flow"))
            if isinstance(raw_flows, dict):
                flows = [raw_flows]
            elif isinstance(raw_flows, list):
                flows = raw_flows
            else:
                raise ValueError(f"Flow file {path} must define flow or flows")

            for flow in flows:
                if not isinstance(flow, dict) or not flow.get("id"):
                    raise ValueError(f"Flow file {path} must define flow.id (or flows[].id)")
                flow_by_id[str(flow["id"])] = flow

        jobs_by_flow_id: dict[str, list[dict[str, Any]]] = {}
        for path, data in self.relational_discovered_definitions.get(DefinitionType.JOBS, {}).items():
            flow_id = data.get("flow_id")
            if not isinstance(flow_id, str) or not flow_id:
                raise ValueError(f"Jobs file {path} must define non-empty flow_id")
            jobs = data.get("jobs", [])
            if not isinstance(jobs, list):
                raise ValueError(f"Jobs file {path} must define jobs as a list")
            jobs_by_flow_id.setdefault(flow_id, []).extend(jobs)

        contracts_by_flow_id: dict[str, list[dict[str, Any]]] = {}
        for path, data in self.relational_discovered_definitions.get(DefinitionType.LINEAGE_CONTRACT, {}).items():
            flow_id = data.get("flow_id")
            if not isinstance(flow_id, str) or not flow_id:
                raise ValueError(f"Lineage contract file {path} must define non-empty flow_id")
            lineage_contract = data.get("lineage_contract", [])
            if not isinstance(lineage_contract, list):
                raise ValueError(f"Lineage contract file {path} must define lineage_contract as a list")
            contracts_by_flow_id.setdefault(flow_id, []).extend(lineage_contract)

        pipelines: list[dict[str, Any]] = []
        for flow_id in sorted(flow_by_id):
            pipelines.append(
                {
                    "flow": flow_by_id[flow_id],
                    "jobs": jobs_by_flow_id.get(flow_id, []),
                    "lineage_contract": contracts_by_flow_id.get(flow_id, []),
                }
            )
        return pipelines

    def _read_yaml(self, path: Path) -> dict[str, Any]:
        """Read one YAML file and enforce a mapping top-level object."""

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise ValueError(f"Expected top-level mapping in {path}")
        return data

    def _resolve_definition_type(self, path: Path, data: dict[str, Any]) -> DefinitionType:
        """Resolve the governance definition type represented by one YAML file."""

        for key in data:
            try:
                return DefinitionType[key.upper()]
            except KeyError:
                continue

        valid = ", ".join(t.value for t in DefinitionType)
        raise ValueError(f"Unable to classify governance YAML type for file: {path}. Expected keys: {valid}")


def governance_root() -> Path:
    """Return the root directory for governance assets."""

    return Path(__file__).resolve().parent.parent


def load_env_config(env_name: str) -> EnvironmentConfig:
    """Load one environment config file from `governance/configs`."""

    config_path = governance_root() / "configs" / f"{env_name}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config file: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected top-level mapping in {config_path}")
    dh = data.get("datahub", {})
    return EnvironmentConfig(
        gms_server=str(dh["gms_server"]),
        token_env=str(dh["token_env"]),
        env=str(data["env"]),
    )


def load_model(definitions_root: str | Path | None = None) -> GovernanceModel:
    """Load all governance definitions from one folder tree into a model."""

    root = Path(definitions_root) if definitions_root is not None else governance_root() / "definitions"
    if not root.exists():
        raise FileNotFoundError(f"Missing definitions directory: {root}")
    return GovernanceYamlLoader(root).load_model()


def parse_args(default_env: str = "dev") -> argparse.Namespace:
    """Parse shared CLI args and resolve `--env` from `ENV` by default."""

    env_from_var = os.getenv("ENV", default_env).strip().lower()
    if env_from_var not in ALLOWED_ENVS:
        raise SystemExit(
            f"Invalid ENV='{os.getenv('ENV')}'. Allowed values: {', '.join(ALLOWED_ENVS)}"
        )
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", choices=list(ALLOWED_ENVS), default=env_from_var)
    return parser.parse_args()


def token_from_env(token_env_name: str) -> str | None:
    """Resolve an auth token from an environment variable name."""

    token = os.getenv(token_env_name)
    return token if token else None
