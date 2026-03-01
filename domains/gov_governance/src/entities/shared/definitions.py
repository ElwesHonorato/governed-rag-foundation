#!/usr/bin/env python3
"""Typed governance definition models used by application managers."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


@dataclass(frozen=True)
class DomainDefinition:
    id: str
    name: str
    description: str | None
    parent: str | None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "DomainDefinition":
        return cls(
            id=str(payload["id"]),
            name=str(payload["name"]),
            description=payload.get("description"),
            parent=payload.get("parent"),
        )


@dataclass(frozen=True)
class GroupDefinition:
    id: str
    name: str | None
    description: str | None
    admins: list[str]
    members: list[str]
    groups: list[str]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "GroupDefinition":
        return cls(
            id=str(payload["id"]),
            name=payload.get("name"),
            description=payload.get("description"),
            admins=_as_str_list(payload.get("admins")),
            members=_as_str_list(payload.get("members")),
            groups=_as_str_list(payload.get("groups")),
        )


@dataclass(frozen=True)
class TagDefinition:
    id: str
    name: str
    description: str | None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TagDefinition":
        return cls(
            id=str(payload["id"]),
            name=str(payload["name"]),
            description=payload.get("description"),
        )


@dataclass(frozen=True)
class TermDefinition:
    id: str
    name: str
    description: str | None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TermDefinition":
        return cls(
            id=str(payload["id"]),
            name=str(payload["name"]),
            description=payload.get("description"),
        )


@dataclass(frozen=True)
class DatasetDefinition:
    id: str
    platform: str
    name: str
    description: str | None
    domain: str
    owners: list[str]
    tags: list[str]
    terms: list[str]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "DatasetDefinition":
        return cls(
            id=str(payload["id"]),
            platform=str(payload["platform"]),
            name=str(payload["name"]),
            description=payload.get("description"),
            domain=str(payload["domain"]),
            owners=_as_str_list(payload.get("owners")),
            tags=_as_str_list(payload.get("tags")),
            terms=_as_str_list(payload.get("terms")),
        )


@dataclass(frozen=True)
class FlowDefinition:
    id: str
    platform: str
    description: str | None
    domain: str
    owners: list[str]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "FlowDefinition":
        return cls(
            id=str(payload["id"]),
            platform=str(payload["platform"]),
            description=payload.get("description"),
            domain=str(payload["domain"]),
            owners=_as_str_list(payload.get("owners")),
        )


@dataclass(frozen=True)
class JobDefinition:
    id: str
    description: str | None
    custom_properties: dict[str, str]
    domain: str
    owners: list[str]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "JobDefinition":
        custom_properties = payload.get("custom_properties")
        if not isinstance(custom_properties, dict):
            custom_properties = {}
        return cls(
            id=str(payload["id"]),
            description=payload.get("description"),
            custom_properties=custom_properties,
            domain=str(payload["domain"]),
            owners=_as_str_list(payload.get("owners")),
        )


@dataclass(frozen=True)
class LineageContractDefinition:
    job: str
    inputs: list[str]
    outputs: list[str]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "LineageContractDefinition":
        return cls(
            job=str(payload["job"]),
            inputs=_as_str_list(payload.get("inputs")),
            outputs=_as_str_list(payload.get("outputs")),
        )


@dataclass(frozen=True)
class PipelineDefinition:
    flow: FlowDefinition
    jobs: list[JobDefinition]
    lineage_contract: list[LineageContractDefinition]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "PipelineDefinition":
        flow_payload = payload.get("flow", {})
        jobs_payload = payload.get("jobs", [])
        lineage_payload = payload.get("lineage_contract", [])
        return cls(
            flow=FlowDefinition.from_mapping(flow_payload),
            jobs=[
                JobDefinition.from_mapping(job_payload)
                for job_payload in jobs_payload
                if isinstance(job_payload, Mapping)
            ],
            lineage_contract=[
                LineageContractDefinition.from_mapping(contract_payload)
                for contract_payload in lineage_payload
                if isinstance(contract_payload, Mapping)
            ],
        )
