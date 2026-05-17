# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 eifel42.dev
"""
Architecture contract: no function-local import statements outside
`TYPE_CHECKING` blocks.

Lazy imports inside function bodies hide dependencies, break static analysis,
and indicate circular-import problems that should be solved via dependency
inversion. Only `if TYPE_CHECKING:` guarded imports are allowed at non-module
scope.
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "fhs"

# TODO AP 9: Eliminate lazy imports via DI/Protocol inversion.
# New files must have all imports at module top-level. Existing violations
# are tracked here and must shrink until this set is empty.
KNOWN_VIOLATIONS: set[str] = {
    "fhs/application/blockchain_case_study_service.py",
    "fhs/application/calculation_service.py",
    "fhs/application/decision_operations.py",
    "fhs/application/delivery_analysis_operations.py",
    "fhs/application/multi_year_analysis_operations.py",
    "fhs/application/scenario_service.py",
    "fhs/core/model/config/delivery.py",
    "fhs/core/services/financial/calculator.py",
    "fhs/core/services/optimization/risk/scenario_reduction.py",
    "fhs/core/services/risk/calculator.py",
    "fhs/core/services/simulation/__init__.py",
    "fhs/notebook/__init__.py",
    "fhs/notebook/glossary.py",
    "fhs/plotting/simulation.py",
    "fhs/presentation/notebook/charts/distributions.py",
    "fhs/presentation/notebook/charts/forecast.py",
    "fhs/presentation/notebook/styling.py",
    "fhs/presentation/notebook/widgets/_capital_budgeting.py",
    "fhs/presentation/notebook/widgets/_distribution.py",
    "fhs/presentation/notebook/widgets/_primitives.py",
    "fhs/presentation/notebook/widgets/_risk.py",
    "fhs/presentation/notebook/widgets/_styles.py",
}


def _is_type_checking_block(node: ast.If) -> bool:
    """Return True when the if-branch is `if TYPE_CHECKING:`."""
    test = node.test
    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
        return True
    # `if typing.TYPE_CHECKING:`
    return (
        isinstance(test, ast.Attribute)
        and test.attr == "TYPE_CHECKING"
        and isinstance(test.value, ast.Name)
        and test.value.id == "typing"
    )


class _FunctionLocalImportVisitor(ast.NodeVisitor):
    """Collect import statements that appear inside function/method bodies."""

    def __init__(self) -> None:
        self.violations: list[int] = []
        self._inside_function: int = 0
        self._inside_type_checking: bool = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._inside_function += 1
        self.generic_visit(node)
        self._inside_function -= 1

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_If(self, node: ast.If) -> None:
        if _is_type_checking_block(node) and self._inside_function == 0:
            old = self._inside_type_checking
            self._inside_type_checking = True
            self.generic_visit(node)
            self._inside_type_checking = old
        else:
            self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        if self._inside_function > 0 and not self._inside_type_checking:
            self.violations.append(node.lineno)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if self._inside_function > 0 and not self._inside_type_checking:
            self.violations.append(node.lineno)


def test_no_function_local_imports() -> None:
    """No import statements inside function/method bodies (except TYPE_CHECKING).

    Files in KNOWN_VIOLATIONS are pre-existing lazy-import violations scheduled
    for cleanup in AP 9. New files must not introduce function-local imports.
    """
    new_violations: list[str] = []
    resolved: list[str] = []

    for py_file in sorted(SRC_ROOT.rglob("*.py")):
        if "__pycache__" in py_file.parts:
            continue

        rel_str = str(py_file.relative_to(SRC_ROOT.parent))

        source = py_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            continue

        visitor = _FunctionLocalImportVisitor()
        visitor.visit(tree)

        is_known = rel_str in KNOWN_VIOLATIONS
        if visitor.violations and not is_known:
            for lineno in visitor.violations:
                new_violations.append(f"{rel_str}:{lineno}")
        if not visitor.violations and is_known:
            resolved.append(rel_str)

    messages: list[str] = []
    if new_violations:
        details = "\n".join(f"  - {v}" for v in new_violations)
        messages.append(
            "NEW function-local imports detected "
            "(break circular imports via DI/Protocol instead):\n" + details
        )
    if resolved:
        details = "\n".join(f"  - {v}" for v in resolved)
        messages.append(
            "Resolved lazy-import files — remove from KNOWN_VIOLATIONS:\n" + details
        )

    if messages:
        assert False, "\n\n".join(messages)
