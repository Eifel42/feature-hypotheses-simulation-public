# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 eifel42.dev
"""
Architecture contract: public methods in core/ and application/ must not
return plain `dict` or `dict[str, Any]`.

Domain and application services must return typed Value Objects (Pydantic
models, dataclasses, NamedTuples, TypedDicts with field names) so that callers
are statically checked and the API is self-documenting.

Allowed exceptions:
- Serialisation utilities (files containing "serial", "yaml", "json" in path)
- `__init__` and `__repr__` methods
- Private methods (name starts with `_`)
- Methods whose return annotation explicitly names a TypedDict subclass
  (detected heuristically: annotation is not a bare `dict`).
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "fhs"

_SERIALISATION_KEYWORDS = {"serial", "yaml", "json", "export", "schema"}
_ALLOWED_METHOD_NAMES = {"__init__", "__repr__", "__str__", "__eq__", "__hash__"}

# TODO AP 2: Replace dict return types with typed Value Objects.
# New public methods in core/ and application/ must not return plain dict.
# Existing violations are tracked here and must shrink until this set is empty.
KNOWN_VIOLATIONS: set[str] = {
    "fhs/application/advanced_portfolio_service.py",
    "fhs/application/blockchain_case_study_service.py",
    "fhs/application/board_recommendation_service.py",
    "fhs/application/decision_operations.py",
    "fhs/application/delivery_analysis_operations.py",
    "fhs/application/dtos.py",
    "fhs/application/optimization_service.py",
    "fhs/application/portfolio_context.py",
    "fhs/application/portfolio_facade.py",
    "fhs/application/risk_layers_operations.py",
    "fhs/core/services/assessment/feature_assessment.py",
    "fhs/core/services/assessment/ranking.py",
    "fhs/core/model/config/scenario.py",
    "fhs/core/model/repositories.py",
    "fhs/core/model/scenario_config.py",
    "fhs/core/model/value_objects/simulation_result.py",
    "fhs/core/services/monte_carlo/correlation.py",
    "fhs/core/services/monte_carlo/engine.py",
    "fhs/core/services/optimization/domain/portfolio_result.py",
    "fhs/core/services/optimization/risk/delivery_analyzer.py",
    "fhs/core/services/portfolio/analysis.py",
    "fhs/core/services/portfolio/decision_support.py",
    "fhs/core/services/portfolio/optimizer.py",
    "fhs/core/services/portfolio/scenarios.py",
    "fhs/core/services/portfolio/utils.py",
    "fhs/core/services/portfolio/views.py",
    "fhs/core/services/reporting/po_summary.py",
    "fhs/core/services/reporting/portfolio_reporting.py",
    "fhs/core/services/reporting/stress_test.py",
    "fhs/core/services/reporting/year1_risk.py",
    "fhs/core/services/risk/calculator.py",
    "fhs/core/services/risk/component_risk.py",
    "fhs/core/services/risk/interpreter.py",
    "fhs/core/services/risk/layer_simulation.py",
    "fhs/core/services/risk/portfolio_layers.py",
    "fhs/core/services/risk/shapley.py",
    "fhs/core/services/risk/sprint_overrun.py",
    "fhs/core/services/simulation/simulator.py",
}


def _is_dict_return(annotation: ast.expr | None) -> bool:
    """Return True when the annotation is a bare dict or dict[str, Any]."""
    if annotation is None:
        return False

    # `dict` — bare name
    if isinstance(annotation, ast.Name) and annotation.id == "dict":
        return True

    # `Dict` from typing
    if isinstance(annotation, ast.Name) and annotation.id == "Dict":
        return True

    # `dict[..., ...]` — subscript
    if (
        isinstance(annotation, ast.Subscript)
        and isinstance(annotation.value, ast.Name)
        and annotation.value.id in ("dict", "Dict")
    ):
        return True

    # Stringified annotations: `"dict"` or `"dict[str, Any]"`
    if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
        val = annotation.value.strip()
        if val == "dict" or val.startswith("dict[") or val.startswith("Dict["):
            return True

    return False


class _DictReturnVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.violations: list[int] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name in _ALLOWED_METHOD_NAMES:
            self.generic_visit(node)
            return
        if node.name.startswith("_"):
            self.generic_visit(node)
            return
        if _is_dict_return(node.returns):
            self.violations.append(node.lineno)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]


def _is_serialisation_file(path: Path) -> bool:
    parts = {p.lower() for p in path.parts}
    name = path.stem.lower()
    return any(kw in name or kw in parts for kw in _SERIALISATION_KEYWORDS)


def test_domain_returns_typed_vos() -> None:
    """Public methods in core/ and application/ must not return plain dict.

    Files in KNOWN_VIOLATIONS are pre-existing violations scheduled for
    cleanup in AP 2. New public methods must return typed Value Objects.
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
            if _is_serialisation_file(py_file):
                continue

            rel_str = str(py_file.relative_to(SRC_ROOT.parent))

            source = py_file.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue

            visitor = _DictReturnVisitor()
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
            "NEW public methods returning plain dict detected "
            "(use typed Value Objects / TypedDict instead):\n" + details
        )
    if resolved:
        details = "\n".join(f"  - {v}" for v in resolved)
        messages.append(
            "Resolved dict-return files — remove from KNOWN_VIOLATIONS:\n" + details
        )

    if messages:
        assert False, "\n\n".join(messages)
