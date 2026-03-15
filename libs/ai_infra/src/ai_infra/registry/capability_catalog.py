"""Capability catalog loader."""

from __future__ import annotations

import json
from pathlib import Path

from ai_infra.contracts.capability_descriptor import CapabilityDescriptor


class CapabilityCatalog:
    """Loads capability metadata from a file-backed catalog."""

    def __init__(self, catalog_path: str) -> None:
        self._catalog_path = Path(catalog_path)

    def load(self) -> list[CapabilityDescriptor]:
        raw_items = json.loads(self._catalog_path.read_text())
        return [
            CapabilityDescriptor(
                name=item["name"],
                category=item["category"],
                backend_kind=item["backend_kind"],
                version=item["version"],
                risk_classification=item["risk_classification"],
                input_schema_ref=item["input_schema_ref"],
                output_schema_ref=item["output_schema_ref"],
                side_effect_flag=item.get("side_effect_flag", False),
                preconditions=tuple(item.get("preconditions", [])),
                postconditions=tuple(item.get("postconditions", [])),
                invariants=tuple(item.get("invariants", [])),
            )
            for item in raw_items
        ]
