#!/usr/bin/env python3
"""Dataset governance manager."""

from __future__ import annotations

from typing import Any

from datahub.sdk import Dataset

from entities.shared.context import DatasetManagerContext


class DatasetManager:
    """Apply dataset definitions and metadata assignments."""

    def __init__(self, governance_def_ctx: DatasetManagerContext) -> None:
        """Store shared governance execution context."""

        self.governance_def_ctx = governance_def_ctx

    def apply(self, datasets: list[dict[str, Any]]) -> None:
        """Upsert all datasets with domain, owners, tags, and terms."""

        for dataset in datasets:
            self.governance_def_ctx.client.entities.upsert(
                Dataset(
                    platform=dataset["platform"],
                    name=dataset["name"],
                    env=self.governance_def_ctx.env,
                    description=dataset.get("description"),
                    domain=self.governance_def_ctx.domain_urns[dataset["domain"]],
                    owners=[self.governance_def_ctx.group_urns[group_id] for group_id in dataset.get("owners", [])],
                    tags=[self.governance_def_ctx.tag_urns[tag_id] for tag_id in dataset.get("tags", [])],
                    terms=[self.governance_def_ctx.term_urns[term_id] for term_id in dataset.get("terms", [])],
                )
            )
            print(f"upserted dataset {dataset['id']}")
