#!/usr/bin/env python3
"""Dataset governance manager."""

from __future__ import annotations

from typing import Any

from entities.shared.context import GovernanceContext


class DatasetManager:
    """Apply dataset definitions and metadata assignments."""

    def __init__(self, ctx: GovernanceContext) -> None:
        """Store shared governance execution context."""

        self.ctx = ctx

    def apply(self, datasets: list[dict[str, Any]]) -> None:
        """Upsert all datasets with domain, owners, tags, and terms."""

        from datahub.sdk import Dataset

        for dataset in datasets:
            self.ctx.client.entities.upsert(
                Dataset(
                    platform=dataset["platform"],
                    name=dataset["name"],
                    env=self.ctx.env_label,
                    description=dataset.get("description"),
                    domain=self.ctx.refs.domain_urns[dataset["domain"]],
                    owners=[self.ctx.refs.group_urns[group_id] for group_id in dataset.get("owners", [])],
                    tags=[self.ctx.refs.tag_urns[tag_id] for tag_id in dataset.get("tags", [])],
                    terms=[self.ctx.refs.term_urns[term_id] for term_id in dataset.get("terms", [])],
                )
            )
            print(f"upserted dataset {dataset['id']}")
