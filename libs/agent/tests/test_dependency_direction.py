from __future__ import annotations

import ast
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOTS = {
    "agent_settings": REPO_ROOT / "libs/agent/settings/src/agent_settings",
    "ai_infra": REPO_ROOT / "libs/agent/core/src/ai_infra",
    "agent_platform": REPO_ROOT / "libs/agent/platform/src/agent_platform",
}
ALLOWED_IMPORTS = {
    "agent_settings": {"agent_settings"},
    "ai_infra": {"ai_infra"},
    "agent_platform": {"agent_platform", "ai_infra", "agent_settings"},
}


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _import_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


class DependencyDirectionTest(unittest.TestCase):
    def test_settings_library_is_independent(self) -> None:
        self._assert_allowed_imports("agent_settings")

    def test_core_is_independent(self) -> None:
        self._assert_allowed_imports("ai_infra")

    def test_platform_depends_only_on_core_and_settings(self) -> None:
        self._assert_allowed_imports("agent_platform")

    def _assert_allowed_imports(self, package_name: str) -> None:
        allowed = ALLOWED_IMPORTS[package_name]
        violations: list[str] = []

        for path in _iter_python_files(PACKAGE_ROOTS[package_name]):
            disallowed = sorted(
                (PACKAGE_ROOTS.keys() & _import_roots(path)) - allowed
            )
            if disallowed:
                imports = ", ".join(disallowed)
                violations.append(f"{path.relative_to(REPO_ROOT)} -> {imports}")

        if violations:
            self.fail(
                f"{package_name} violates libs/agent dependency direction:\n"
                + "\n".join(violations)
            )
