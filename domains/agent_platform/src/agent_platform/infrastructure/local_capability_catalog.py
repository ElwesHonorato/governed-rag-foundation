"""Local config loaders."""

from __future__ import annotations

import json
from pathlib import Path


def load_skill_registry(path: str) -> dict[str, dict[str, object]]:
    """Load skill definitions from JSON-in-YAML."""

    return json.loads(Path(path).read_text())
