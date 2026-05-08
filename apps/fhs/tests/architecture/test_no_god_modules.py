# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 eifel42.dev
"""
Architecture contract: no Python source file exceeds 400 lines of code.

God-modules (>400 LOC) violate the Single-Responsibility Principle and make
auditing and onboarding harder. This test enforces the LOC budget per file so
that every module can be understood in under 5 minutes.

Counting method: non-empty, non-comment lines (logical LOC), to avoid
penalising well-documented files.
"""

from __future__ import annotations

from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "fhs"

MAX_LOC = 400

# TODO AP 1: Split these God-modules by domain responsibility.
# New files must stay under 400 LOC. Existing violations are tracked here
# and must shrink with each sprint until this set is empty.
KNOWN_VIOLATIONS: set[str] = {
    "fhs/application/blockchain_case_study_service.py",
    "fhs/application/decision_operations.py",
    "fhs/application/delivery_analysis_operations.py",
    "fhs/application/optimization_service.py",
    "fhs/application/portfolio_facade.py",  # deprecated module
    "fhs/core/services/financial/calculator.py",
    "fhs/core/services/optimization/solvers/cvar_milp_solver.py",
    "fhs/core/services/portfolio/decision_support.py",
    "fhs/core/services/portfolio/optimizer.py",
    "fhs/core/services/risk/calculator.py",
    "fhs/core/services/risk/portfolio_layers.py",
    "fhs/notebook/__init__.py",
    "fhs/plotting/reporting.py",
    "fhs/presentation/notebook/charts/capital_budgeting.py",
    "fhs/presentation/notebook/charts/distributions.py",
    "fhs/presentation/notebook/charts/forecast.py",
    "fhs/presentation/notebook/charts/interactive.py",
    "fhs/presentation/notebook/charts/risk.py",
    "fhs/presentation/notebook/formatters.py",
    "fhs/presentation/notebook/widgets/_capital_budgeting.py",
    "fhs/presentation/notebook/widgets/_portfolio.py",
    "fhs/presentation/notebook/widgets/_risk.py",
}


def _logical_loc(path: Path) -> int:
    """Count non-empty, non-comment lines in a Python source file."""
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            count += 1
    return count


def test_no_god_modules() -> None:
    """Every .py file in src/fhs must have ≤400 logical lines of code.

    Files in KNOWN_VIOLATIONS are pre-existing god-modules scheduled for
    refactoring in AP 1. New files must stay under the limit immediately.
    """
    new_violations: list[str] = []
    resolved: list[str] = []

    for py_file in sorted(SRC_ROOT.rglob("*.py")):
        if "__pycache__" in py_file.parts:
            continue
        rel_str = str(py_file.relative_to(SRC_ROOT.parent))
        loc = _logical_loc(py_file)
        is_over_limit = loc > MAX_LOC
        is_known = rel_str in KNOWN_VIOLATIONS

        if is_over_limit and not is_known:
            new_violations.append(f"{rel_str} ({loc} LOC, limit {MAX_LOC})")
        if not is_over_limit and is_known:
            resolved.append(rel_str)

    messages: list[str] = []
    if new_violations:
        details = "\n".join(f"  - {v}" for v in new_violations)
        messages.append(
            f"NEW god-modules detected (>{MAX_LOC} LOC) — add to AP 1 backlog:\n"
            + details
        )
    if resolved:
        details = "\n".join(f"  - {v}" for v in resolved)
        messages.append(
            "Resolved god-modules — remove from KNOWN_VIOLATIONS in this test:\n"
            + details
        )

    if messages:
        assert False, "\n\n".join(messages)
