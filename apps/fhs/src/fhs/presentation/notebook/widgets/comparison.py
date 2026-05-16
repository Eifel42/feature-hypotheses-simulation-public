# Project: FHS (Feature Hypotheses Simulation)
# Copyright: Eifel42 Stefan Zils 2026
# License: See LICENSE and README.md
#
# Disclaimer: This software is provided "as is", without warranty of any kind,
# express or implied, including but not limited to the warranties of
# merchantability, fitness for a particular purpose, and noninfringement.
# In no event shall the authors or copyright holders be liable for any claim,
# damages or other liability, whether in an action of contract, tort or
# otherwise, arising from, out of or in connection with the software or the
# use or other dealings in the software.

"""Comparison and decision-grid widget components."""

from __future__ import annotations

from ..styling import COLORS
from ..template_engine import render
from ._helpers import _footer_block
from .cards import section_card


def _solver_column(
    label: str,
    selected: list[str],
    total_cost: float,
    expected_business_value: float,
    var95: float,
    roi: float,
    portfolios_checked: int,
    runtime_sec: float,
    *,
    accent: str | None = None,
) -> str:
    """Return one column of a solver comparison card."""
    c = accent or COLORS.primary
    feats = ", ".join(sorted(selected))
    return render(
        "comparison/solver_column.html.j2",
        label=label,
        accent=c,
        feats=feats,
        total_cost=total_cost,
        expected_business_value=expected_business_value,
        var95=var95,
        roi=roi,
        portfolios_checked=portfolios_checked,
        runtime_sec=runtime_sec,
    )


def _verdict_parts(
    solvers: tuple,
    labels: list[str],
    reference_index: int,
    ref_features: set[str],
    ref_var_95: float,
) -> list[str]:
    parts: list[str] = []
    for j, solver in enumerate(solvers):
        if j == reference_index:
            continue
        diff_pct = (
            abs(solver["portfolio_var_95"] - ref_var_95) / ref_var_95 * 100
            if ref_var_95 > 0
            else 0
        )
        if set(solver["recommended_features"]) == ref_features:
            parts.append(f"<b>{labels[j]}</b>: same selection")
        else:
            parts.append(
                f"<b>{labels[j]}</b>: different selection (VaR gap {diff_pct:.2f}%)"
            )
    return parts


def solver_comparison_card(
    *solvers: dict,
    title: str = "Solver Comparison",
    labels: list[str] | None = None,
    accents: list[str] | None = None,
    reference_index: int = 0,
) -> str:
    """Return a side-by-side solver comparison card with verdict."""
    default_labels = [
        "Exact Solver (exhaustive search)",
        "ILP Solver (linear programming)",
        "Hybrid Solver (greedy + simulation)",
    ]
    default_accents = [COLORS.primary, COLORS.accent, COLORS.secondary]

    _labels = labels or default_labels[: len(solvers)]
    _accents = accents or default_accents[: len(solvers)]

    cols_html = ""
    for i, solver in enumerate(solvers):
        cols_html += _solver_column(
            _labels[i],
            solver["recommended_features"],
            solver["total_cost"],
            solver["portfolio_expected"],
            solver["portfolio_var_95"],
            solver["roi"],
            solver.get("combinations_evaluated", solver.get("candidates_evaluated", 0)),
            solver["computation_time_sec"],
            accent=_accents[i],
        )

    ref = solvers[reference_index]
    ref_features = set(ref["recommended_features"])
    agreements = [
        set(s["recommended_features"]) == ref_features
        for j, s in enumerate(solvers)
        if j != reference_index
    ]

    if all(agreements):
        verdict_color = COLORS.secondary
        verdict_text = "✔ All solvers selected the <b>same portfolio</b>."
    else:
        verdict_color = COLORS.warning
        verdict_text = "⚠ " + " &nbsp;|&nbsp; ".join(
            _verdict_parts(
                solvers, _labels, reference_index, ref_features, ref["portfolio_var_95"]
            )
        )

    return section_card(
        title,
        f'<div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:16px;">{cols_html}</div>'
        f"{_footer_block(verdict_text, padding='12px 18px', font_size='14px', border_left_color=verdict_color)}",
    )


def decision_grid(
    items: list[dict],
    *,
    title: str | None = None,
    footer: str | None = None,
) -> str:
    """Return a multi-column decision grid with accent-topped cards."""
    return render(
        "comparison/decision_grid.html.j2",
        items=items,
        title=title,
        footer=footer,
    )
