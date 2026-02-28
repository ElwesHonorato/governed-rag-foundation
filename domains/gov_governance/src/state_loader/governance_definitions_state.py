#!/usr/bin/env python3
"""Shared config/model loading utilities for governance scripts."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable, Mapping

from pipeline_common.helpers.file_reader import FileReader
from pipeline_common.helpers.file_system_helper import FileSystemHelper


ALLOWED_ENVS = ("DEV", "PROD")


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
        """Load one environment config file from `domains/gov_governance/configs`."""

        config_path = cls._governance_dir() / "configs" / f"{env_name.lower()}.yaml"
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

        env_label = env_name.strip().upper()
        if env_label not in ALLOWED_ENVS:
            raise SystemExit(
                f"Invalid env '{env_name}'. Allowed values: {', '.join(ALLOWED_ENVS)}"
            )

        env_settings = cls._load_env_settings(env_label)
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
        self.files_by_definition_type: dict[DefinitionType, dict[Path, dict[str, Any]]] = {}

    def add(self, definition_type: DefinitionType, path: Path, data: dict[str, Any]) -> None:
        self.files_by_definition_type.setdefault(definition_type, {})[path] = data

    def build_payloads(self) -> dict[DefinitionType, list[dict[str, Any]]]:
        return {
            definition_type: self._items_for_standalone_type(definition_type)
            for definition_type in self.files_by_definition_type
        }

    def _items_for_standalone_type(self, definition_type: DefinitionType) -> list[dict[str, Any]]:
        key = definition_type.standalone_key
        standalone_entities_definitions: list[dict[str, Any]] = []
        standalone_type_payloads = self.files_by_definition_type.get(definition_type, {})
        for payload in standalone_type_payloads.values():
            standalone_entities_definitions.extend(payload.get(key, []))
        return standalone_entities_definitions


class RelationalDefinitions:
    """Store discovered relational definitions and build pipelines."""

    def __init__(self) -> None:
        self.files_by_definition_type: dict[DefinitionType, dict[Path, dict[str, Any]]] = {}
        self.flow_by_id: dict[str, tuple[Path, dict[str, Any]]] = {}
        self.jobs_by_flow_id: dict[str, list[dict[str, Any]]] = {}
        self.contracts_by_flow_id: dict[str, list[dict[str, Any]]] = {}

    def add(self, definition_type: DefinitionType, path: Path, data: dict[str, Any]) -> None:
        """Register one relational YAML payload by type and source path.

        Input structure:
        - definition_type: one of FLOW/JOBS/LINEAGE_CONTRACT
        - path: filesystem path to YAML file
        - data: parsed YAML mapping for that file

        Output structure:
        - None (mutates internal store `self.files_by_definition_type`)
        """
        self.files_by_definition_type.setdefault(definition_type, {})[path] = data

    def build_pipelines(self) -> list[dict[str, Any]]:
        """Build normalized pipeline payloads from relational definition files.

        Input structure:
        - Uses `self.files_by_definition_type` internal mapping:
          {DefinitionType: {Path: dict[str, Any]}}

        Output structure:
        - list[dict[str, Any]] where each item is:
          {
            "flow": dict[str, Any],
            "jobs": list[dict[str, Any]],
            "lineage_contract": list[dict[str, Any]],
          }
        """
        self._index_relational_definitions()
        return self._assemble_pipelines()

    def _index_relational_definitions(self) -> None:
        """Collect all relational definitions and index them by flow context.

        Input structure:
        - Uses `self.files_by_definition_type` for FLOW/JOBS/LINEAGE_CONTRACT files.

        Output structure:
        - None (mutates `self.flow_by_id`, `self.jobs_by_flow_id`, and `self.contracts_by_flow_id`)
        """
        collectors: dict[DefinitionType, Callable[[Path, dict[str, Any]], None]] = {
            DefinitionType.FLOW: self._index_flows,
            DefinitionType.JOBS: self._index_jobs,
            DefinitionType.LINEAGE_CONTRACT: self._index_lineage_contracts,
        }
        for definition_type, indexer in collectors.items():
            self._apply_indexer(definition_type, indexer)

    def _apply_indexer(
        self,
        definition_type: DefinitionType,
        indexer: Callable[[Path, dict[str, Any]], None],
    ) -> None:
        for path, data in self._iter_definition_files(definition_type):
            indexer(path, data)

    def _iter_definition_files(self, definition_type: DefinitionType) -> list[tuple[Path, dict[str, Any]]]:
        """Return all stored files for a given relational definition type.

        Input structure:
        - definition_type: FLOW/JOBS/LINEAGE_CONTRACT

        Output structure:
        - list[tuple[Path, dict[str, Any]]]
        """
        return list(self.files_by_definition_type.get(definition_type, {}).items())

    def _index_flows(
        self,
        path: Path,
        data: dict[str, Any],
    ) -> None:
        """Index all flows from a single flow file.

        Input structure:
        - path/data: one FLOW file payload
        - uses `self.flow_by_id`: mutable {flow_id: (source_path, flow_def)}

        Output structure:
        - None (mutates `self.flow_by_id`)
        """
        raw_flows = data.get("flows", data.get("flow", []))
        if isinstance(raw_flows, dict):
            flows = [raw_flows]
        else:
            flows = raw_flows
        for flow in flows:
            flow_id = flow.get("id")
            if flow_id in self.flow_by_id:
                original_path = self.flow_by_id[flow_id][0]
                raise ValueError(
                    f"Duplicate flow id '{flow_id}' found in {original_path} and {path}"
                )
            self.flow_by_id[flow_id] = (path, flow)

    def _index_jobs(
        self,
        path: Path,
        data: dict[str, Any],
    ) -> None:
        """Index all jobs from one jobs file into grouped job indexes."""
        self._index_items_by_flow(
            path=path,
            data=data,
            items_key="jobs",
            target_by_flow_id=self.jobs_by_flow_id,
        )

    def _index_lineage_contracts(
        self,
        path: Path,
        data: dict[str, Any],
    ) -> None:
        """Index all lineage contracts from one contract file into grouped indexes."""
        self._index_items_by_flow(
            path=path,
            data=data,
            items_key="lineage_contract",
            target_by_flow_id=self.contracts_by_flow_id,
        )

    def _index_items_by_flow(
        self,
        path: Path,
        data: Mapping[str, Any],
        items_key: str,
        target_by_flow_id: dict[str, list[dict[str, Any]]],
    ) -> None:
        """Index one list field from a relational file into a flow-grouped target."""
        flow_id = data.get("flow_id")
        self._assert_known_flow_id(flow_id, path)
        items = data.get(items_key, [])
        self._append_flow_items(flow_id, items, target_by_flow_id)

    def _append_flow_items(
        self,
        flow_id: str,
        items: list[Mapping[str, Any]],
        target_by_flow_id: dict[str, list[dict[str, Any]]],
    ) -> None:
        """Append items to the list bucket associated with one flow id."""
        for item in items:
            target_by_flow_id.setdefault(flow_id, []).append(item)

    def _assert_known_flow_id(self, flow_id: str, path: Path) -> None:
        """Ensure flow_id exists in known flow ids.

        Input structure:
        - flow_id: str
        - path: source file path for error context

        Output structure:
        - None (raises ValueError on missing reference)
        """
        if flow_id not in self.flow_by_id:
            raise ValueError(f"File {path} references unknown flow_id '{flow_id}'")

    @staticmethod
    def _assert_unique_scoped_id(
        item_id: str,
        scope_id: str,
        seen_ids_by_scope: dict[str, set[str]],
        item_kind: str,
        scope_kind: str,
    ) -> None:
        """Ensure identifier uniqueness within a specific parent scope.

        Input structure:
        - item_id: str
        - scope_id: str
        - seen_ids_by_scope: mutable {scope_id: {item_id, ...}}
        - item_kind/scope_kind: labels for error messages

        Output structure:
        - None (mutates `seen_ids_by_scope`)
        """
        scoped_seen_ids = seen_ids_by_scope.setdefault(scope_id, set())
        if item_id in scoped_seen_ids:
            raise ValueError(f"Duplicate {item_kind} '{item_id}' found for {scope_kind} '{scope_id}'")
        scoped_seen_ids.add(item_id)

    def _assemble_pipelines(self) -> list[dict[str, Any]]:
        """Assemble deterministic pipeline list from indexed relational definitions.

        Input structure:
        - self.flow_by_id: {flow_id: (source_path, flow_def)}
        - self.jobs_by_flow_id: {flow_id: [job_def, ...]}
        - self.contracts_by_flow_id: {flow_id: [contract_def, ...]}

        Output structure:
        - list[dict[str, Any]] sorted by flow_id, with each item:
          {"flow": dict, "jobs": list[dict], "lineage_contract": list[dict]}
        """
        pipelines: list[dict[str, Any]] = []
        for flow_id in sorted(self.flow_by_id):
            flow_jobs = self.jobs_by_flow_id.get(flow_id, [])
            flow_contracts = self.contracts_by_flow_id.get(flow_id, [])
            pipelines.append(
                {
                    "flow": self.flow_by_id[flow_id][1],
                    "jobs": flow_jobs,
                    "lineage_contract": flow_contracts,
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


def resolve_env(default_env: str = "DEV") -> str:
    """Resolve environment from `ENV` and validate it."""

    env_from_var = os.getenv("ENV", default_env).strip().upper()
    if env_from_var not in ALLOWED_ENVS:
        raise SystemExit(
            f"Invalid ENV='{os.getenv('ENV')}'. Allowed values: {', '.join(ALLOWED_ENVS)}"
        )
    return env_from_var
