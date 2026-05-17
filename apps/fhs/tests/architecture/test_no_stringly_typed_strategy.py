# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 eifel42.dev
"""
Architecture contract: no stringly-typed `strategy`, `solver`, or `metric`
parameters in public function/method signatures in core/ and application/.

These must be typed via `OptimizationStrategy`, `SolverType`, or
`RiskMetricKind` enums — not bare `str`. This prevents invalid values from
reaching deep into the simulation pipeline.

Scanned annotation forms:
  - `strategy: str`
  - `solver: str`
  - `metric: str`
  - `acceptance_model: str`

Defaults with string literals are also flagged:
  - `strategy: str = "var_floor"`
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "fhs"

# Parameter names that must NOT be typed as plain `str`
_STRINGLY_TYPED_PARAMS = {"strategy", "solver", "metric", "acceptance_model"}

# Modules allowed to keep `str` (e.g., CLI parsing or YAML deserialization)
_ALLOWLIST_MODULES = {
    "cli.py",
}

# TODO AP 6: Replace str with OptimizationStrategy / SolverType / RiskMetricKind enums.
# New files in core/ and application/ must use enums. Existing violations are
# tracked here and must shrink with each sprint until this set is empty.
KNOWN_VIOLATIONS: set[str] = {
    "fhs/core/model/entities/feature.py",
    "fhs/core/services/optimization/solvers/exact_solver.py",
    "fhs/core/services/optimization/solvers/greedy_solver.py",
    "fhs/core/services/optimization/solvers/ilp_solver.py",
    "fhs/core/services/portfolio/decision_support.py",
    "fhs/core/services/portfolio/optimizer.py",
    "fhs/core/services/portfolio/views.py",
    "fhs/core/services/risk/attribution.py",
    "fhs/core/services/risk/shapley.py",
    "fhs/application/advanced_portfolio_service.py",
    "fhs/application/decision_operations.py",
    "fhs/application/optimization_service.py",
    "fhs/application/risk_analysis_operations.py",
}


def _is_plain_str_annotation(annotation: ast.expr | None) -> bool:
    """Return True when the annotation resolves to bare `str`."""
    if annotation is None:
        return False
    # `str`
    if isinstance(annotation, ast.Name) and annotation.id == "str":
        return True
    # `"str"` (stringified forward reference)
    return isinstance(annotation, ast.Constant) and annotation.value == "str"


class _StringlyTypedVisitor(ast.NodeVisitor):
    """Collect function arguments typed as plain `str` for forbidden param names."""

    def __init__(self) -> None:
        self.violations: list[int] = []

    def _check_args(self, args: ast.arguments) -> None:
        for arg in args.args + args.posonlyargs + args.kwonlyargs:
            if arg.arg in _STRINGLY_TYPED_PARAMS and _is_plain_str_annotation(
                arg.annotation
            ):
                self.violations.append(
                    arg.col_offset if hasattr(arg, "col_offset") else 0
                )
                # Use lineno attribute
                self.violations[-1] = arg.lineno  # type: ignore[attr-defined]

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_args(node.args)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]


def test_no_stringly_typed_strategy() -> None:
    """strategy/solver/metric params in core/ and application/ must use enums, not str.

    Files in KNOWN_VIOLATIONS are pre-existing violations scheduled for
    cleanup in AP 6. New files must use enums immediately.
    """
    new_violations: list[str] = []
    resolved: list[str] = []

    scan_roots = [
        SRC_ROOT / "core",
        SRC_ROOT / "application",
    ]

    for root in scan_roots:
        if not root.exists():
            continue
        for py_file in sorted(root.rglob("*.py")):
            if "__pycache__" in py_file.parts:
                continue
            if py_file.name in _ALLOWLIST_MODULES:
                continue

            rel_str = str(py_file.relative_to(SRC_ROOT.parent))

            source = py_file.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue

            visitor = _StringlyTypedVisitor()
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
            "NEW stringly-typed parameters detected "
            "(use OptimizationStrategy / SolverType / RiskMetricKind enums):\n"
            + details
        )
    if resolved:
        details = "\n".join(f"  - {v}" for v in resolved)
        messages.append(
            "Resolved stringly-typed files — remove from KNOWN_VIOLATIONS:\n" + details
        )

    if messages:
        assert False, "\n\n".join(messages)
