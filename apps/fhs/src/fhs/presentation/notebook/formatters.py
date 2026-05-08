#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

"""
Delivery Risk Analysis Formatters

Reusable formatting utilities for delivery risk portfolio tables.
Extracts repetitive row-building logic from notebooks into testable functions.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np

from fhs.presentation.notebook.styling import COLORS


@dataclass(frozen=True)
class _AggMetrics:
    expected: float
    var_95: float
    p95: float


_SOLVER_LABELS = {
    "exact": "Exact",
    "hybrid": "Hybrid",
    "ilp": "ILP",
}


def _investment_summary_row(
    *,
    annual_installment: float,
    development_cost: float,
    alt_bg: str,
) -> str:
    year1_pct = annual_installment / development_cost * 100
    return (
        f"<tr style='background:{alt_bg};border-top:2px solid {COLORS.border}'>"
        f"<td style='padding:6px 10px;font-weight:600'>Total Investment</td>"
        f"<td style='padding:6px 10px;text-align:right;font-weight:600'>"
        f"€{development_cost:,.0f}</td>"
        f"<td colspan='3' style='padding:6px 10px;font-size:11px;color:{COLORS.neutral}'>"
        f"Year-1 charge: €{annual_installment:,.0f} ({year1_pct:.0f}% of total)</td>"
        f"</tr>"
    )


def _installment_summary_row(
    *,
    annual_installment: float,
    installment_years: int,
    development_cost: float,
) -> str:
    dep_label = (
        f"Installment ({installment_years} yrs)"
        if installment_years > 1
        else "Annual Installment"
    )
    dep_context = (
        f"€{annual_installment:,.0f}/yr — straight-line over {installment_years} years"
        if installment_years > 1
        else "Straight-line cost charge per year"
    )
    border_top = (
        f"border-top:1px solid {COLORS.border}" if development_cost <= 0 else ""
    )
    return (
        f"<tr style='background:{COLORS.background};{border_top}'>"
        f"<td style='padding:6px 10px;font-weight:600;color:{COLORS.danger}'>"
        f"{dep_label}</td>"
        f"<td style='padding:6px 10px;text-align:right;color:{COLORS.danger}'>"
        f"€{annual_installment:,.0f}</td>"
        f"<td colspan='3' style='padding:6px 10px;font-size:11px;color:{COLORS.neutral}'>"
        f"{dep_context}</td>"
        f"</tr>"
    )


def _scenario_metrics(values: Any) -> _AggMetrics:
    if len(values) == 0:
        return _AggMetrics(expected=0.0, var_95=0.0, p95=0.0)
    return _AggMetrics(
        expected=float(np.mean(values)),
        var_95=float(np.percentile(values, 5)),
        p95=float(np.percentile(values, 95)),
    )


def _multi_year_rows_html(result: Any, alt_bg: str) -> str:
    rows_html = ""
    for i, yr in enumerate(result.years):
        bg = alt_bg if i % 2 == 0 else COLORS.background
        spread = f"±{yr.spread_pct:.0f}%" if yr.expected else ""
        rows_html += (
            f"<tr style='background:{bg}'>"
            f"<td style='padding:6px 10px;font-weight:600'>Year {yr.year}</td>"
            f"<td style='padding:6px 10px;text-align:right'>€{yr.expected:,.0f}</td>"
            f"<td style='padding:6px 10px;text-align:right;color:{COLORS.warning}'>"
            f"€{yr.var_95:,.0f}</td>"
            f"<td style='padding:6px 10px;text-align:right;color:{COLORS.secondary}'>"
            f"€{yr.p95:,.0f}</td>"
            f"<td style='padding:6px 10px;text-align:right'>{spread}</td>"
            f"</tr>"
        )
    return rows_html


def _multi_year_summary_rows(result: Any, alt_bg: str) -> str:
    yearly = [y.scenarios for y in result.years]
    cum = _scenario_metrics(sum(yearly) if yearly else np.array([]))
    rate = result.discount_rate
    npv_arr = (
        sum(y / (1 + rate) ** (t + 1) for t, y in enumerate(yearly))
        if yearly
        else np.array([])
    )
    npv = _scenario_metrics(npv_arr)

    return (
        f"<tr style='border-top:2px solid {COLORS.primary};background:{alt_bg}'>"
        f"<td style='padding:6px 10px;font-weight:700'>3Y Total</td>"
        f"<td style='padding:6px 10px;text-align:right;font-weight:700'>€{cum.expected:,.0f}</td>"
        f"<td style='padding:6px 10px;text-align:right;color:{COLORS.warning}'>"
        f"€{cum.var_95:,.0f}</td>"
        f"<td style='padding:6px 10px;text-align:right;color:{COLORS.secondary}'>"
        f"€{cum.p95:,.0f}</td>"
        f"<td></td></tr>"
        f"<tr style='background:{COLORS.background}'>"
        f"<td style='padding:6px 10px;font-weight:700'>NPV {rate:.0%}</td>"
        f"<td style='padding:6px 10px;text-align:right;font-weight:700'>€{npv.expected:,.0f}</td>"
        f"<td style='padding:6px 10px;text-align:right;color:{COLORS.warning}'>"
        f"€{npv.var_95:,.0f}</td>"
        f"<td style='padding:6px 10px;text-align:right;color:{COLORS.secondary}'>"
        f"€{npv.p95:,.0f}</td>"
        f"<td></td></tr>"
    )


def format_budget_status(
    features: list,
    budget: float,
    *,
    source: str | None = None,
    scenarios: int | None = None,
) -> dict[str, Any]:
    """Summarise budget fit in simple beginner-friendly language.

    Returns a structured summary that presentation helpers can render in a
    consistent way across notebooks.
    """
    if not features:
        note_parts = []
        if source:
            note_parts.append(f"Source: {source}")
        if scenarios is not None:
            note_parts.append(f"{scenarios:,} Monte Carlo scenarios per feature")
        return {
            "level": "warning",
            "message": "No features are loaded yet, so the budget cannot be checked.",
            "rows": [("Configured budget", f"EUR {budget:,.0f}", None)],
            "note": " | ".join(note_parts) if note_parts else None,
        }

    ordered = sorted(features, key=lambda feature: feature.development_cost)
    total_cost = sum(feature.development_cost for feature in ordered)
    cheapest = ordered[0]
    affordable = [feature for feature in ordered if feature.development_cost <= budget]

    affordable_names = (
        ", ".join(feature.name.split(": ", 1)[-1] for feature in affordable)
        if affordable
        else "None"
    )
    cheapest_label = cheapest.name.split(": ", 1)[-1]

    rows = [
        ("Configured budget", f"EUR {budget:,.0f}", None),
        ("Cost of all features", f"EUR {total_cost:,.0f}", None),
        (
            "Cheapest feature",
            f"{cheapest_label} — EUR {cheapest.development_cost:,.0f}",
            None,
        ),
        (
            "Affordable now",
            f"{len(affordable)} of {len(features)} ({affordable_names})",
            None,
        ),
    ]

    note_parts = []
    if source:
        note_parts.append(f"Source: {source}")
    if scenarios is not None:
        note_parts.append(f"{scenarios:,} Monte Carlo scenarios per feature")

    if budget < cheapest.development_cost:
        level = "danger"
        message = (
            f"Budget is below the cheapest feature. The lowest-cost option is "
            f"{cheapest_label} at EUR {cheapest.development_cost:,.0f}. "
            "You cannot start a single hypothesis yet."
        )
    elif budget < total_cost:
        level = "warning"
        message = (
            f"Budget is below the cost of the full portfolio. "
            f"You can fund {len(affordable)} of {len(features)} features now, "
            "so you need to choose the first step."
        )
    else:
        level = "success"
        message = f"Budget can cover all {len(features)} features in this scenario."

    return {
        "level": level,
        "message": message,
        "rows": rows,
        "note": " | ".join(note_parts) if note_parts else None,
        "total_cost": total_cost,
        "cheapest_cost": cheapest.development_cost,
        "affordable_count": len(affordable),
    }


def format_multi_year_result(
    result: Any,
    annual_installment: float = 0.0,
    installment_years: int = 0,
    development_cost: float = 0.0,
) -> str:
    """Render a MultiYearResult as an HTML table card.

    Parameters
    ----------
    result:
        ``MultiYearResult`` object with per-year simulation data.
    annual_installment:
        Annual installment charge in EUR (straight-line). When > 0, an
        additional "Annual Installment" row is shown below the NPV row.
    installment_years:
        Installment period in years. When > 1, the installment row label
        includes the period (e.g. "Installment (3 yrs)").
    development_cost:
        Total development cost in EUR. When > 0, a "Total Investment" row is
        shown above the installment row, including the year-1 charge share.

    Returns a standalone HTML string — testable without IPython.
    """
    hdr_bg = COLORS.primary
    hdr_fg = COLORS.background
    alt_bg = COLORS.surface

    rows_html = _multi_year_rows_html(result, alt_bg)
    rows_html += _multi_year_summary_rows(result, alt_bg)

    if development_cost > 0 and annual_installment > 0:
        rows_html += _investment_summary_row(
            annual_installment=annual_installment,
            development_cost=development_cost,
            alt_bg=alt_bg,
        )

    if annual_installment > 0:
        rows_html += _installment_summary_row(
            annual_installment=annual_installment,
            installment_years=installment_years,
            development_cost=development_cost,
        )

    n_scenarios = len(result.years[0].scenarios) if result.years else 0

    return (
        f"<div style='border:1px solid {COLORS.border};border-radius:8px;overflow:auto;"
        f"border-left:4px solid {hdr_bg};margin:8px 0'>"
        f"<table style='width:100%;border-collapse:collapse;font-size:13px'>"
        f"<caption style='background:{hdr_bg};color:{hdr_fg};padding:8px 10px;"
        f"text-align:left;font-weight:700;font-size:14px'>"
        f"📅 {result.feature_name} — Multi-Year Simulation"
        f"<span style='float:right;font-weight:400;font-size:11px'>"
        f"{n_scenarios:,} scenarios / year</span></caption>"
        f"<tr style='background:{hdr_bg};color:{hdr_fg}'>"
        f"<th style='padding:6px 10px;text-align:left'>Year</th>"
        f"<th style='padding:6px 10px;text-align:right'>Expected</th>"
        f"<th style='padding:6px 10px;text-align:right'>Floor 95%</th>"
        f"<th style='padding:6px 10px;text-align:right'>Ceiling P95</th>"
        f"<th style='padding:6px 10px;text-align:right'>Spread</th></tr>"
        f"{rows_html}</table></div>"
    )


def format_feature_rows(
    delivery_risk_result: dict[str, Any],
) -> list[tuple[str, str, str]]:
    """
    Format per-feature delivery risk details as table rows.

    Extracts feature name, non-delivery risk percentage, and simulated
    delivery rate from the analyze_delivery_risk() result.

    Args:
        delivery_risk_result: Output from PortfolioOptimizer.analyze_delivery_risk()

    Returns:
        List of tuples (name, risk_pct, delivered_pct) for display
    """
    rows = []
    for feature in delivery_risk_result.get("features", []):
        name = feature["name"]
        # Strip "Section: " prefix if present (from advanced-features.yaml)
        if ": " in name:
            name = name.split(": ", 1)[1]

        risk_pct = f"{feature['non_delivery_risk'] * 100:.0f}%"
        delivered_pct = f"{feature['delivered_pct'] * 100:.1f}%"

        rows.append((name, risk_pct, delivered_pct))

    return rows


def format_summary_row(
    label: str,
    level_1: dict[str, Any],
    level_3: dict[str, Any],
) -> tuple[str, str, str, str, str, str, str]:
    """
    Format one summary row comparing three levels of risk.

    Builds a row for the three-level risk comparison table:
    L1 (Market only) → L2 (+ Delivery) → L3 (+ Shock)

    Args:
        label: Solver name (e.g., "Exact", "ILP")
        level_1: Result from analyze_delivery_risk() [market baseline]
        level_3: Result from analyze_delivery_risk() with shock parameters

    Returns:
        Tuple of formatted strings for the summary table row
    """
    return (
        label,
        f"EUR {level_1['market_expected']:,.0f}",
        f"EUR {level_1['market_var_95']:,.0f}",
        f"EUR {level_1['simulated_expected']:,.0f}",
        f"EUR {level_1['simulated_var_95']:,.0f}",
        f"EUR {level_3['shocked_expected']:,.0f}",
        f"EUR {level_3['shocked_var_95']:,.0f}",
    )


def format_multi_budget_rows(
    budgets: list[float],
    budget_results: dict[float, dict[str, Any]],
) -> list[tuple]:
    """
    Format multi-budget comparison rows for Step 6.

    Converts a dict of budget-keyed analysis results into displayable rows.

    Args:
        budgets: List of budget amounts (EUR)
        budget_results: Dict mapping budget amount → {
            'exact': l1_result, 'ilp': l2_result
        }

    Returns:
        List of tuples formatted for show.sensitivity() display
    """
    rows = []

    for budget in budgets:
        if budget not in budget_results:
            continue

        analysis = budget_results[budget]
        for solver_name in ("exact", "ilp"):
            if solver_name not in analysis:
                continue

            l1 = analysis[solver_name].get("l1")
            l3 = analysis[solver_name].get("l3")
            n_feat = analysis[solver_name].get("feature_count", 0)

            if l1 is None or l3 is None or n_feat == 0:
                continue

            rows.append(
                (
                    f"EUR {budget / 1000:.0f}k",
                    _SOLVER_LABELS.get(solver_name, solver_name.title()),
                    str(n_feat),
                    f"EUR {l1['market_expected']:,.0f}",
                    f"EUR {l1['market_var_95']:,.0f}",
                    f"EUR {l1['simulated_var_95']:,.0f} ({l1['var_delta_pct']:+.1f}%)",
                    f"EUR {l3['shocked_var_95']:,.0f} ({l3['shocked_var_delta_pct']:+.1f}%)",
                )
            )

    return rows


def format_budget_risk_drop_rows(
    budgets: list[float],
    budget_results: dict[float, dict[str, Any]],
) -> list[tuple[str, str, str, str, str]]:
    """Format budget rows focused on downside erosion across risk layers.

    Args:
        budgets: Budget amounts (EUR) used as sample planning points.
        budget_results: Output from ``PortfolioOptimizer.analyze_budget_risk_profiles``.

    Returns:
        List of tuples for display in a notebook sensitivity table.
    """
    rows = []

    for budget in budgets:
        analysis = budget_results.get(budget, {})
        for solver_name in ("exact", "ilp"):
            solver_data = analysis.get(solver_name)
            if not solver_data:
                continue

            level_1 = solver_data["l1"]
            level_3 = solver_data["l3"]
            rows.append(
                (
                    f"EUR {budget / 1000:.0f}k",
                    _SOLVER_LABELS.get(solver_name, solver_name.title()),
                    f"{solver_data['feature_count']}",
                    f"{level_1['var_delta_pct']:+.1f}%",
                    f"{level_3['shocked_var_delta_pct']:+.1f}%",
                )
            )

    return rows


def format_llp_overview_rows(
    features: list,
    simulation_results: dict,
) -> list[tuple[str, str, str, str, str]]:
    """Format feature-level LLP overview rows for display.

    Shows each feature's LLP, expected business value, business value at risk from LLP,
    and a risk-zone indicator.

    Args:
        features: List of Feature objects
        simulation_results: Dict mapping feature name to SimulationResult

    Returns:
        List of tuples (name, llp, expected_value, value_at_risk, zone) for display
    """
    rows = []
    for f in features:
        result = simulation_results.get(f.name)
        if result is None:
            continue

        short = f.name.split(": ", 1)[-1] if ": " in f.name else f.name
        llp = f.likelihood_of_non_delivery
        value = result.expected_business_value
        at_risk = value * llp

        if llp <= 0.15:
            zone = "🟢 Low"
        elif llp <= 0.30:
            zone = "🟡 Medium"
        else:
            zone = "🔴 High"

        rows.append(
            (
                short,
                f"{llp * 100:.0f}%",
                f"EUR {value:,.0f}",
                f"EUR {at_risk:,.0f}",
                zone,
            )
        )

    return rows


def format_risk_layer_rows(
    level_1: dict[str, Any],
    level_3: dict[str, Any],
) -> list[tuple[str, str, str, str, str]]:
    """Format the three risk levels as simple rows with traffic-light indicators.

    Returns a compact summary showing level, expected, VaR 95%, and delta
    compared to L1 baseline.

    Args:
        level_1: Result from analyze_delivery_risk (market + delivery)
        level_3: Result from analyze_delivery_risk with shock params

    Returns:
        List of three tuples, one per risk level.
    """
    l1_exp = level_1["market_expected"]
    l1_var = level_1["market_var_95"]
    l2_exp = level_1["simulated_expected"]
    l2_var = level_1["simulated_var_95"]
    l3_exp = level_3["shocked_expected"]
    l3_var = level_3["shocked_var_95"]

    def _delta(new: float, base: float) -> str:
        if base == 0:
            return "—"
        return f"{(new / base - 1) * 100:+.1f}%"

    return [
        (
            "🟢 L1 — Market",
            f"EUR {l1_exp:,.0f}",
            f"EUR {l1_var:,.0f}",
            "Baseline",
            "Baseline",
        ),
        (
            "🟡 L2 — + Delivery (LLP)",
            f"EUR {l2_exp:,.0f}",
            f"EUR {l2_var:,.0f}",
            _delta(l2_exp, l1_exp),
            _delta(l2_var, l1_var),
        ),
        (
            "🔴 L3 — + Shock",
            f"EUR {l3_exp:,.0f}",
            f"EUR {l3_var:,.0f}",
            _delta(l3_exp, l1_exp),
            _delta(l3_var, l1_var),
        ),
    ]
