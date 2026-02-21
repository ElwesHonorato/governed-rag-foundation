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

from pipeline_common.helpers.file_reader import FileReader
from pipeline_common.helpers.file_system_helper import FileSystemHelper


ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
ALLOWED_ENVS = ("dev", "prod")


@dataclass(frozen=True)
class EnvironmentSettings:
    """Runtime config for a target DataHub environment."""

    gms_server: str
    token: str | None


@dataclass(frozen=True)
class GovernanceDefinitionSnapshot:
    """In-memory representation of governance YAML definitions."""

    domains: list[dict[str, Any]]
    groups: list[dict[str, Any]]
    tags: list[dict[str, Any]]
    terms: list[dict[str, Any]]
    datasets: list[dict[str, Any]]
    pipelines: list[dict[str, Any]]


@dataclass(frozen=True)
class GovernanceState:
    """Resolved governance runtime state for a selected environment."""

    env_settings: EnvironmentSettings
    governance_definitions_snapshot: GovernanceDefinitionSnapshot


class GovernanceStateLoader:
    """Load governance runtime state from local configuration definitions."""

    @classmethod
    def _governance_dir(cls) -> Path:
        """Resolve the governance directory from this module location."""

        return FileSystemHelper.find_dir_upwards(Path(__file__), n=2)

    @classmethod
    def _load_env_settings(cls, env_name: str) -> EnvironmentSettings:
        """Load one environment config file from `governance/configs`."""

        config_path = cls._governance_dir() / "configs" / f"{env_name}.yaml"
        data = FileReader(path=config_path).read()
        datahub_env_config = data.get("datahub", {})
        token_env_name = str(datahub_env_config["token_env"])
        return EnvironmentSettings(
            gms_server=str(datahub_env_config["gms_server"]),
            token=os.getenv(token_env_name) or None,
        )

    @classmethod
    def load_definition_snapshot(cls) -> GovernanceDefinitionSnapshot:
        """Load all governance definitions from one folder tree into a snapshot."""

        definitions_dir = cls._governance_dir() / "definitions"
        discoverer = GovernanceDefinitionDiscoverer(
            definitions_root=definitions_dir,
            standalone_discovered_definitions=StandaloneDefinitions(),
            relational_discovered_definitions=RelationalDefinitions(),
        )
        discoverer.load()
        return GovernanceDefinitionSnapshot(
            domains=discoverer.standalone_payloads.get(DefinitionType.DOMAINS, []),
            groups=discoverer.standalone_payloads.get(DefinitionType.GROUPS, []),
            tags=discoverer.standalone_payloads.get(DefinitionType.TAGS, []),
            terms=discoverer.standalone_payloads.get(DefinitionType.TERMS, []),
            datasets=discoverer.standalone_payloads.get(DefinitionType.DATASETS, []),
            pipelines=discoverer.pipelines,
        )

    @classmethod
    def load(cls, env_name: str) -> GovernanceState:
        """Load environment settings and governance definitions for one environment."""

        env_settings = cls._load_env_settings(env_name)
        governance_definitions_snapshot = cls.load_definition_snapshot()
        return GovernanceState(
            env_settings=env_settings,
            governance_definitions_snapshot=governance_definitions_snapshot,
        )


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


class StandaloneDefinitions:
    """Store and aggregate discovered standalone definitions."""

    def __init__(self) -> None:
        self.by_type: dict[DefinitionType, dict[Path, dict[str, Any]]] = {}

    def add(self, definition_type: DefinitionType, path: Path, data: dict[str, Any]) -> None:
        self.by_type.setdefault(definition_type, {})[path] = data

    def build_payloads(self) -> dict[DefinitionType, list[dict[str, Any]]]:
        return {
            definition_type: self._items_for_standalone_type(definition_type)
            for definition_type in self.by_type
        }

    def _items_for_standalone_type(self, definition_type: DefinitionType) -> list[dict[str, Any]]:
        key = definition_type.standalone_key
        standalone_entities_definitions: list[dict[str, Any]] = []
        standalone_type_payloads = self.by_type.get(definition_type, {})
        for payload in standalone_type_payloads.values():
            standalone_entities_definitions.extend(payload.get(key, []))
        return standalone_entities_definitions


class RelationalDefinitions:
    """Store discovered relational definitions and build pipelines."""

    def __init__(self) -> None:
        self.by_type: dict[DefinitionType, dict[Path, dict[str, Any]]] = {}

    def add(self, definition_type: DefinitionType, path: Path, data: dict[str, Any]) -> None:
        self.by_type.setdefault(definition_type, {})[path] = data

    def build_pipelines(self) -> list[dict[str, Any]]:
        flow_by_id: dict[str, dict[str, Any]] = {}
        for path, data in self.by_type.get(DefinitionType.FLOW, {}).items():
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
        for path, data in self.by_type.get(DefinitionType.JOBS, {}).items():
            flow_id = data.get("flow_id")
            if not isinstance(flow_id, str) or not flow_id:
                raise ValueError(f"Jobs file {path} must define non-empty flow_id")
            jobs = data.get("jobs", [])
            if not isinstance(jobs, list):
                raise ValueError(f"Jobs file {path} must define jobs as a list")
            jobs_by_flow_id.setdefault(flow_id, []).extend(jobs)

        contracts_by_flow_id: dict[str, list[dict[str, Any]]] = {}
        for path, data in self.by_type.get(DefinitionType.LINEAGE_CONTRACT, {}).items():
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


class GovernanceDefinitionDiscoverer:
    """Discover governance YAML and partition into standalone/relational classes."""

    def __init__(
        self,
        definitions_root: Path,
        standalone_discovered_definitions: StandaloneDefinitions,
        relational_discovered_definitions: RelationalDefinitions,
        definition_type: DefinitionType | None = None,
    ) -> None:
        self.definitions_root = definitions_root
        self.definition_type = definition_type
        self.standalone_discovered_definitions = standalone_discovered_definitions
        self.relational_discovered_definitions = relational_discovered_definitions
        self.standalone_payloads: dict[DefinitionType, list[dict[str, Any]]] = {}
        self.pipelines: list[dict[str, Any]] = []

    def load(self) -> None:
        definition_paths = sorted(self.definitions_root.rglob("*.yaml"))

        for path in definition_paths:
            data = FileReader(path=path).read()
            definition_type = self._resolve_definition_type(path, data)
            if self.definition_type is not None and definition_type != self.definition_type:
                continue
            if definition_type.standalone_key is None:
                self.relational_discovered_definitions.add(definition_type, path, data)
            else:
                self.standalone_discovered_definitions.add(definition_type, path, data)

        self.standalone_payloads = self.standalone_discovered_definitions.build_payloads()
        self.pipelines = self.relational_discovered_definitions.build_pipelines()

    def _resolve_definition_type(self, path: Path, data: dict[str, Any]) -> DefinitionType:
        for key in data:
            try:
                return DefinitionType[key.upper()]
            except KeyError:
                continue
        valid = ", ".join(t.value for t in DefinitionType)
        raise ValueError(f"Unable to classify governance YAML type for file: {path}. Expected keys: {valid}")


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
