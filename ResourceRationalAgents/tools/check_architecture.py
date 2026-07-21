"""Reject forbidden imports between the planning domain's hexagonal roles."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "resource_rational_agents" / "planning"
PREFIX = "resource_rational_agents.planning"

FORBIDDEN = {
    "domain": (
        f"{PREFIX}.application",
        f"{PREFIX}.adapters",
        f"{PREFIX}.composition",
    ),
    "application": (f"{PREFIX}.adapters", f"{PREFIX}.composition"),
    "adapters": (f"{PREFIX}.composition",),
}


def imported_modules(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return tuple(modules)


def main() -> int:
    violations: list[str] = []
    for role, forbidden_prefixes in FORBIDDEN.items():
        role_root = PACKAGE / role
        for path in sorted(role_root.rglob("*.py")):
            for imported in imported_modules(path):
                if imported.startswith(forbidden_prefixes):
                    relative = path.relative_to(ROOT)
                    violations.append(f"{relative}: forbidden dependency on {imported}")
    if violations:
        print("\n".join(violations))
        return 1
    print("Architecture check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

