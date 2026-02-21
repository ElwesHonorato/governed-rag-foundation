#!/usr/bin/env python3
"""Shared config/model loading utilities for governance scripts."""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
ALLOWED_ENVS = ("dev", "prod")


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


def governance_root() -> Path:
    """Return the root directory for governance assets."""

    return Path(__file__).resolve().parent.parent


def _read_yaml(path: Path) -> dict[str, Any]:
    """Read one YAML file and enforce a mapping top-level object."""

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected top-level mapping in {path}")
    return data


def load_env_config(env_name: str) -> EnvironmentConfig:
    """Load one environment config file from `governance/configs`."""

    config_path = governance_root() / "configs" / f"{env_name}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config file: {config_path}")
    data = _read_yaml(config_path)
    dh = data.get("datahub", {})
    return EnvironmentConfig(
        gms_server=str(dh["gms_server"]),
        token_env=str(dh["token_env"]),
        env=str(data["env"]),
    )


def load_model() -> GovernanceModel:
    """Load all governance definitions into one model object."""

    root = governance_root()
    domains = _read_yaml(root / "definitions" / "domains.yaml").get("domains", [])
    groups = _read_yaml(root / "definitions" / "groups.yaml").get("groups", [])
    tags = _read_yaml(root / "definitions" / "tags.yaml").get("tags", [])
    terms = _read_yaml(root / "definitions" / "glossary.yaml").get("terms", [])
    datasets: list[dict[str, Any]] = []
    for path in sorted((root / "definitions" / "datasets").glob("*.yaml")):
        datasets.extend(_read_yaml(path).get("datasets", []))

    pipelines: list[dict[str, Any]] = []
    for path in sorted((root / "definitions" / "pipelines").glob("*.yaml")):
        pipelines.append(_read_yaml(path))

    return GovernanceModel(
        domains=list(domains),
        groups=list(groups),
        tags=list(tags),
        terms=list(terms),
        datasets=datasets,
        pipelines=pipelines,
    )


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
