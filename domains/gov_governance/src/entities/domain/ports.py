#!/usr/bin/env python3
"""Domain governance write ports."""

from __future__ import annotations

from typing import Protocol


class DomainCatalogWriter(Protocol):
    """Port for persisting governance domain metadata."""

    def upsert_domain(
        self,
        *,
        entity_urn: str,
        name: str,
        description: str | None,
        parent_domain_urn: str | None,
    ) -> None:
        """Upsert one domain entity record."""
