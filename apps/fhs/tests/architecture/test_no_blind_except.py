# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 eifel42.dev
"""
Architecture contract: no blind `except Exception` or bare `except` outside
system boundaries (CLI entry point, notebook façade).

Catching broad exceptions swallows programming errors and makes debugging
impossible. Domain and application code must catch only specific exception
types. System-boundary modules are allow-listed.
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "fhs"

# Modules that are allowed to catch broad exceptions (system boundaries)
_ALLOWLIST_SUFFIXES = {
    "cli.py",
    "__init__.py",  # notebook façade: optional-import try/except ImportError is OK
}

# TODO AP 10: Fix blind except-clauses in these files.
# New files must use specific exception types. Existing violations are tracked
# here and must shrink with each sprint until this set is empty.
KNOWN_VIOLATIONS: set[str] = {
    "fhs/core/model/events.py",
    "fhs/core/services/simulation/simulator.py",
    "fhs/infra/repositories/yaml_repository.py",
}


def _has_blind_except(tree: ast.AST) -> list[int]:
    """Return line numbers of blind except-clauses in the AST."""
    lines: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        # bare `except:` → type is None
        if node.type is None:
            lines.append(node.lineno)
            continue
        # `except Exception:` or `except BaseException:`
        if isinstance(node.type, ast.Name) and node.type.id in (
            "Exception",
            "BaseException",
        ):
            lines.append(node.lineno)
        # `except (Exception, ...):` tuple form
        if isinstance(node.type, ast.Tuple):
            for elt in node.type.elts:
                if isinstance(elt, ast.Name) and elt.id in (
                    "Exception",
                    "BaseException",
                ):
                    lines.append(node.lineno)
    return lines


def test_no_blind_except() -> None:
    """No bare/broad except-clauses in domain or application code.

    Files in KNOWN_VIOLATIONS are pre-existing violations scheduled for
    cleanup in AP 10. New files must use specific exception types immediately.
    """
    new_violations: list[str] = []
    resolved: list[str] = []

    for py_file in sorted(SRC_ROOT.rglob("*.py")):
        if "__pycache__" in py_file.parts:
            continue
        if py_file.name in _ALLOWLIST_SUFFIXES:
            continue

        rel_str = str(py_file.relative_to(SRC_ROOT.parent))

        source = py_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            continue

        lines = _has_blind_except(tree)
        is_known = rel_str in KNOWN_VIOLATIONS

        if lines and not is_known:
            for lineno in lines:
                new_violations.append(f"{rel_str}:{lineno}")
        if not lines and is_known:
            resolved.append(rel_str)

    messages: list[str] = []
    if new_violations:
        details = "\n".join(f"  - {v}" for v in new_violations)
        messages.append(
            "NEW blind except-clauses detected (catch specific exceptions):\n" + details
        )
    if resolved:
        details = "\n".join(f"  - {v}" for v in resolved)
        messages.append(
            "Resolved blind-except files — remove from KNOWN_VIOLATIONS:\n" + details
        )

    if messages:
        assert False, "\n\n".join(messages)
