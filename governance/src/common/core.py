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
        """Register one relational YAML payload by type and source path.

        Input structure:
        - definition_type: one of FLOW/JOBS/LINEAGE_CONTRACT
        - path: filesystem path to YAML file
        - data: parsed YAML mapping for that file

        Output structure:
        - None (mutates internal store `self.by_type`)
        """
        self.by_type.setdefault(definition_type, {})[path] = data

    def build_pipelines(self) -> list[dict[str, Any]]:
        """Build normalized pipeline payloads from relational definition files.

        Input structure:
        - Uses `self.by_type` internal mapping:
          {DefinitionType: {Path: dict[str, Any]}}

        Output structure:
        - list[dict[str, Any]] where each item is:
          {
            "flow": dict[str, Any],
            "jobs": list[dict[str, Any]],
            "lineage_contract": list[dict[str, Any]],
          }
        """
        flow_by_id = self._collect_flows_by_id()
        jobs_by_flow_id = self._collect_jobs_by_flow_id(set(flow_by_id))
        contracts_by_flow_id = self._collect_contracts_by_flow_id(set(flow_by_id))
        return self._assemble_pipelines(flow_by_id, jobs_by_flow_id, contracts_by_flow_id)

    def _collect_flows_by_id(self) -> dict[str, dict[str, Any]]:
        """Collect all flows and index them by `flow.id`.

        Input structure:
        - FLOW files in `self.by_type[DefinitionType.FLOW]`
        - each file can contain:
          {"flow": {...}} or {"flows": [{...}, ...]}

        Output structure:
        - dict[str, dict[str, Any]] as {flow_id: flow_definition}
        """
        flow_by_id: dict[str, dict[str, Any]] = {}
        flow_source_by_id: dict[str, Path] = {}
        for path, data in self._iter_definition_files(DefinitionType.FLOW):
            self._merge_flows_from_file(path, data, flow_by_id, flow_source_by_id)
        return flow_by_id

    def _collect_jobs_by_flow_id(self, known_flow_ids: set[str]) -> dict[str, list[dict[str, Any]]]:
        """Collect jobs grouped by `flow_id` with referential checks.

        Input structure:
        - known_flow_ids: set[str] of valid flow ids
        - JOBS file shape:
          {"flow_id": "<flow-id>", "jobs": [{...}, ...]}

        Output structure:
        - dict[str, list[dict[str, Any]]] as {flow_id: [job_definition, ...]}
        """
        jobs_by_flow_id: dict[str, list[dict[str, Any]]] = {}
        job_ids_by_flow_id: dict[str, set[str]] = {}

        for path, data in self._iter_definition_files(DefinitionType.JOBS):
            self._merge_jobs_from_file(
                path=path,
                data=data,
                known_flow_ids=known_flow_ids,
                jobs_by_flow_id=jobs_by_flow_id,
                job_ids_by_flow_id=job_ids_by_flow_id,
            )
        return jobs_by_flow_id

    def _collect_contracts_by_flow_id(self, known_flow_ids: set[str]) -> dict[str, list[dict[str, Any]]]:
        """Collect lineage contracts grouped by `flow_id` with referential checks.

        Input structure:
        - known_flow_ids: set[str] of valid flow ids
        - LINEAGE_CONTRACT file shape:
          {"flow_id": "<flow-id>", "lineage_contract": [{...}, ...]}

        Output structure:
        - dict[str, list[dict[str, Any]]] as {flow_id: [contract_definition, ...]}
        """
        contracts_by_flow_id: dict[str, list[dict[str, Any]]] = {}
        contract_jobs_by_flow_id: dict[str, set[str]] = {}

        for path, data in self._iter_definition_files(DefinitionType.LINEAGE_CONTRACT):
            self._merge_contracts_from_file(
                path=path,
                data=data,
                known_flow_ids=known_flow_ids,
                contracts_by_flow_id=contracts_by_flow_id,
                contract_jobs_by_flow_id=contract_jobs_by_flow_id,
            )
        return contracts_by_flow_id

    def _iter_definition_files(self, definition_type: DefinitionType) -> list[tuple[Path, dict[str, Any]]]:
        """Return all stored files for a given relational definition type.

        Input structure:
        - definition_type: FLOW/JOBS/LINEAGE_CONTRACT

        Output structure:
        - list[tuple[Path, dict[str, Any]]]
        """
        return list(self.by_type.get(definition_type, {}).items())

    @staticmethod
    def _required_string(value: Any, error_message: str) -> str:
        """Validate that value is a non-empty string and return it.

        Input structure:
        - value: Any
        - error_message: str

        Output structure:
        - str (validated non-empty string)
        """
        if not isinstance(value, str) or not value:
            raise ValueError(error_message)
        return value

    def _extract_flow_id(self, path: Path, data: dict[str, Any], file_label: str) -> str:
        """Extract and validate `flow_id` from one relational file payload.

        Input structure:
        - path: source YAML path
        - data: parsed YAML mapping
        - file_label: message prefix (e.g., "Jobs file")

        Output structure:
        - str flow_id
        """
        return self._required_string(data.get("flow_id"), f"{file_label} {path} must define non-empty flow_id")

    def _merge_flows_from_file(
        self,
        path: Path,
        data: dict[str, Any],
        flow_by_id: dict[str, dict[str, Any]],
        flow_source_by_id: dict[str, Path],
    ) -> None:
        """Merge all flows from a single flow file into flow indexes.

        Input structure:
        - path/data: one FLOW file payload
        - flow_by_id: mutable {flow_id: flow_def}
        - flow_source_by_id: mutable {flow_id: source_path}

        Output structure:
        - None (mutates `flow_by_id` and `flow_source_by_id`)
        """
        for flow in self._normalize_flows(path, data):
            flow_id = self._extract_entity_id(flow, "id", f"Flow file {path} must define flow.id (or flows[].id)")
            self._register_unique_entity(
                entity_id=flow_id,
                entity=flow,
                source_path=path,
                target_by_id=flow_by_id,
                source_by_id=flow_source_by_id,
                entity_kind="flow",
            )

    def _merge_jobs_from_file(
        self,
        path: Path,
        data: dict[str, Any],
        known_flow_ids: set[str],
        jobs_by_flow_id: dict[str, list[dict[str, Any]]],
        job_ids_by_flow_id: dict[str, set[str]],
    ) -> None:
        """Merge all jobs from one jobs file into grouped job indexes.

        Input structure:
        - data shape: {"flow_id": str, "jobs": list[dict]}
        - known_flow_ids: set of valid flow ids
        - jobs_by_flow_id: mutable {flow_id: [job_def, ...]}
        - job_ids_by_flow_id: mutable {flow_id: {job_id, ...}}

        Output structure:
        - None (mutates `jobs_by_flow_id` and `job_ids_by_flow_id`)
        """
        flow_id = self._extract_flow_id(path, data, "Jobs file")
        self._assert_known_flow_id(flow_id, known_flow_ids, path, "Jobs file")
        jobs = self._extract_list_field(path, data, "jobs", "Jobs file")
        self._merge_job_definitions(flow_id, path, jobs, jobs_by_flow_id, job_ids_by_flow_id)

    def _merge_job_definitions(
        self,
        flow_id: str,
        path: Path,
        jobs: list[Any],
        jobs_by_flow_id: dict[str, list[dict[str, Any]]],
        job_ids_by_flow_id: dict[str, set[str]],
    ) -> None:
        """Merge validated job definitions for one flow.

        Input structure:
        - flow_id: parent flow id
        - jobs: list[Any] expected as list[dict]
        - jobs_by_flow_id: mutable {flow_id: [job_def, ...]}
        - job_ids_by_flow_id: mutable {flow_id: {job_id, ...}}

        Output structure:
        - None (mutates both indexes)
        """
        for job in jobs:
            self._assert_mapping(job, path, "Jobs file", "job")
            job_id = self._extract_entity_id(job, "id", f"Jobs file {path} must define jobs[].id")
            self._assert_unique_scoped_id(
                item_id=job_id,
                scope_id=flow_id,
                seen_ids_by_scope=job_ids_by_flow_id,
                item_kind="job",
                scope_kind="flow_id",
            )
            jobs_by_flow_id.setdefault(flow_id, []).append(job)

    def _merge_contracts_from_file(
        self,
        path: Path,
        data: dict[str, Any],
        known_flow_ids: set[str],
        contracts_by_flow_id: dict[str, list[dict[str, Any]]],
        contract_jobs_by_flow_id: dict[str, set[str]],
    ) -> None:
        """Merge all lineage contracts from one contract file into grouped indexes.

        Input structure:
        - data shape: {"flow_id": str, "lineage_contract": list[dict]}
        - known_flow_ids: set of valid flow ids
        - contracts_by_flow_id: mutable {flow_id: [contract_def, ...]}
        - contract_jobs_by_flow_id: mutable {flow_id: {job_id, ...}}

        Output structure:
        - None (mutates both indexes)
        """
        flow_id = self._extract_flow_id(path, data, "Lineage contract file")
        self._assert_known_flow_id(flow_id, known_flow_ids, path, "Lineage contract file")
        contracts = self._extract_list_field(path, data, "lineage_contract", "Lineage contract file")
        self._merge_contract_definitions(
            flow_id=flow_id,
            path=path,
            contracts=contracts,
            contracts_by_flow_id=contracts_by_flow_id,
            contract_jobs_by_flow_id=contract_jobs_by_flow_id,
        )

    def _merge_contract_definitions(
        self,
        flow_id: str,
        path: Path,
        contracts: list[Any],
        contracts_by_flow_id: dict[str, list[dict[str, Any]]],
        contract_jobs_by_flow_id: dict[str, set[str]],
    ) -> None:
        """Merge validated contract definitions for one flow.

        Input structure:
        - flow_id: parent flow id
        - contracts: list[Any] expected as list[dict]
        - contracts_by_flow_id: mutable {flow_id: [contract_def, ...]}
        - contract_jobs_by_flow_id: mutable {flow_id: {job_id, ...}}

        Output structure:
        - None (mutates both indexes)
        """
        for contract in contracts:
            self._assert_mapping(contract, path, "Lineage contract file", "lineage_contract")
            job_id = self._extract_entity_id(
                contract,
                "job",
                f"Lineage contract file {path} must define lineage_contract[].job",
            )
            self._assert_unique_scoped_id(
                item_id=job_id,
                scope_id=flow_id,
                seen_ids_by_scope=contract_jobs_by_flow_id,
                item_kind="lineage contract for job",
                scope_kind="flow_id",
            )
            contracts_by_flow_id.setdefault(flow_id, []).append(contract)

    @staticmethod
    def _assert_known_flow_id(flow_id: str, known_flow_ids: set[str], path: Path, file_label: str) -> None:
        """Ensure flow_id exists in known flow ids.

        Input structure:
        - flow_id: str
        - known_flow_ids: set[str]
        - path/file_label: context for error message

        Output structure:
        - None (raises ValueError on missing reference)
        """
        if flow_id not in known_flow_ids:
            raise ValueError(f"{file_label} {path} references unknown flow_id '{flow_id}'")

    @staticmethod
    def _assert_mapping(value: Any, path: Path, file_label: str, field_label: str) -> None:
        """Ensure value is a dictionary/mapping-like YAML object.

        Input structure:
        - value: Any
        - path/file_label/field_label: context for error message

        Output structure:
        - None (raises ValueError if value is not dict)
        """
        if not isinstance(value, dict):
            raise ValueError(f"{file_label} {path} must define {field_label} objects")

    def _extract_list_field(
        self,
        path: Path,
        data: dict[str, Any],
        field_name: str,
        file_label: str,
    ) -> list[Any]:
        """Extract a list field from file payload and validate list type.

        Input structure:
        - data: parsed YAML mapping
        - field_name: key to read
        - path/file_label: context for error message

        Output structure:
        - list[Any]
        """
        field_value = data.get(field_name, [])
        if not isinstance(field_value, list):
            raise ValueError(f"{file_label} {path} must define {field_name} as a list")
        return field_value

    def _normalize_flows(self, path: Path, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Normalize flow payload to `list[dict]` from `flow` or `flows`.

        Input structure:
        - data supports:
          {"flow": dict} or {"flows": list[dict]}

        Output structure:
        - list[dict[str, Any]] of flow definitions
        """
        raw_flows = data.get("flows", data.get("flow"))
        if isinstance(raw_flows, dict):
            flows: list[Any] = [raw_flows]
        elif isinstance(raw_flows, list):
            flows = raw_flows
        else:
            raise ValueError(f"Flow file {path} must define flow or flows")
        normalized_flows: list[dict[str, Any]] = []
        for flow in flows:
            self._assert_mapping(flow, path, "Flow file", "flow")
            normalized_flows.append(flow)
        return normalized_flows

    def _extract_entity_id(self, entity: dict[str, Any], key: str, error_message: str) -> str:
        """Extract and validate a required string identifier field from entity mapping.

        Input structure:
        - entity: dict[str, Any]
        - key: identifier key name (e.g., "id", "job")
        - error_message: str

        Output structure:
        - str identifier value
        """
        return self._required_string(entity.get(key), error_message)

    @staticmethod
    def _register_unique_entity(
        entity_id: str,
        entity: dict[str, Any],
        source_path: Path,
        target_by_id: dict[str, dict[str, Any]],
        source_by_id: dict[str, Path],
        entity_kind: str,
    ) -> None:
        """Insert entity into index while enforcing unique identifier.

        Input structure:
        - entity_id: str
        - entity: dict[str, Any]
        - source_path: Path
        - target_by_id: mutable {id: entity_def}
        - source_by_id: mutable {id: source_path}
        - entity_kind: label for error messages

        Output structure:
        - None (mutates both indexes)
        """
        if entity_id in target_by_id:
            original_path = source_by_id[entity_id]
            raise ValueError(
                f"Duplicate {entity_kind} id '{entity_id}' found in {original_path} and {source_path}"
            )
        target_by_id[entity_id] = entity
        source_by_id[entity_id] = source_path

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

    @staticmethod
    def _assemble_pipelines(
        flow_by_id: dict[str, dict[str, Any]],
        jobs_by_flow_id: dict[str, list[dict[str, Any]]],
        contracts_by_flow_id: dict[str, list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """Assemble deterministic pipeline list from indexed relational definitions.

        Input structure:
        - flow_by_id: {flow_id: flow_def}
        - jobs_by_flow_id: {flow_id: [job_def, ...]}
        - contracts_by_flow_id: {flow_id: [contract_def, ...]}

        Output structure:
        - list[dict[str, Any]] sorted by flow_id, with each item:
          {"flow": dict, "jobs": list[dict], "lineage_contract": list[dict]}
        """
        pipelines: list[dict[str, Any]] = []
        for flow_id in sorted(flow_by_id):
            flow_jobs = sorted(jobs_by_flow_id.get(flow_id, []), key=lambda job: str(job.get("id", "")))
            flow_contracts = sorted(
                contracts_by_flow_id.get(flow_id, []),
                key=lambda contract: str(contract.get("job", "")),
            )
            pipelines.append(
                {
                    "flow": flow_by_id[flow_id],
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
