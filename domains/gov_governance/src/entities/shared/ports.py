#!/usr/bin/env python3
"""Application-side governance write ports."""

from __future__ import annotations

from typing import Protocol


class GovernanceCatalogWriterPort(Protocol):
    """Port for persisting governance entities into the catalog backend."""

    def upsert_domain(
        self,
        *,
        entity_urn: str,
        name: str,
        description: str | None,
        parent_domain_urn: str | None,
    ) -> None:
        """Upsert one domain definition."""

    def upsert_group(
        self,
        *,
        group_urn: str,
        display_name: str | None,
        description: str | None,
        admin_refs: list[str],
        member_refs: list[str],
        group_refs: list[str],
    ) -> None:
        """Upsert one ownership group definition."""

    def upsert_tag(
        self,
        *,
        name: str,
        display_name: str | None,
        description: str | None,
    ) -> None:
        """Upsert one tag definition."""

    def upsert_glossary_term(
        self,
        *,
        entity_urn: str,
        term_id: str,
        name: str,
        definition: str | None,
    ) -> None:
        """Upsert one glossary term definition."""

    def upsert_dataset(
        self,
        *,
        platform: str,
        name: str,
        env: str,
        description: str | None,
        domain: str,
        owners: list[str],
        tags: list[str],
        terms: list[str],
    ) -> None:
        """Upsert one dataset definition."""

    def upsert_flow(
        self,
        *,
        platform: str,
        flow_id: str,
        env: str,
        description: str | None,
        domain: str,
        owners: list[str],
    ) -> None:
        """Upsert one flow definition."""

    def upsert_job(
        self,
        *,
        flow_platform: str,
        flow_id: str,
        env: str,
        job_id: str,
        description: str | None,
        custom_properties: dict[str, str],
        domain: str,
        owners: list[str],
        inlets: list[str],
        outlets: list[str],
    ) -> None:
        """Upsert one job definition."""
