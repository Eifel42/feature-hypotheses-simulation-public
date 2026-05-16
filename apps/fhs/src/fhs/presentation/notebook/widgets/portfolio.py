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

"""Portfolio-focused widget components."""

from __future__ import annotations

from markupsafe import Markup

from ..styling import COLORS
from ..template_engine import render


def selection_card(
    selected_features: list[str],
    metrics: dict,
    *,
    title: str = "Recommended Selection",
    accent: str | None = None,
    excluded_features: list | None = None,
) -> str:
    """Display selected features with portfolio metrics."""
    c = accent or COLORS.secondary
    expected_total = metrics.get("total_expected_business_value", 0.0)

    metrics_rows = (
        f'<tr><th scope="row" style="padding:5px 15px;text-align:left;font-weight:normal;">Expected Business Value:</th>'
        f'<td style="padding:5px 15px;font-weight:bold;">EUR {expected_total:,.0f}</td></tr>'
        f'<tr><th scope="row" style="padding:5px 15px;text-align:left;font-weight:normal;">VaR (95%):</th>'
        f'<td style="padding:5px 15px;font-weight:bold;">EUR {metrics["portfolio_var_95"]:,.0f}</td></tr>'
        f'<tr><th scope="row" style="padding:5px 15px;text-align:left;font-weight:normal;">Risk Ratio:</th>'
        f'<td style="padding:5px 15px;font-weight:bold;">{metrics["portfolio_risk_ratio"]:.1%}</td></tr>'
    )

    if "total_development_cost" in metrics:
        metrics_rows += (
            f'<tr><th scope="row" style="padding:5px 15px;text-align:left;font-weight:normal;">Total Cost:</th>'
            f'<td style="padding:5px 15px;font-weight:bold;">EUR {metrics["total_development_cost"]:,.0f}</td></tr>'
        )
    if "budget_remaining" in metrics:
        metrics_rows += (
            f'<tr><th scope="row" style="padding:5px 15px;text-align:left;font-weight:normal;">Budget Remaining:</th>'
            f'<td style="padding:5px 15px;font-weight:bold;">EUR {metrics["budget_remaining"]:,.0f}</td></tr>'
        )
    if "portfolio_roi" in metrics:
        metrics_rows += (
            f'<tr><th scope="row" style="padding:5px 15px;text-align:left;font-weight:normal;">ROI:</th>'
            f'<td style="padding:5px 15px;font-weight:bold;">{metrics["portfolio_roi"]:.0%}</td></tr>'
        )
    if "portfolio_net_value" in metrics:
        metrics_rows += (
            f'<tr><th scope="row" style="padding:5px 15px;text-align:left;font-weight:normal;">Net Value:</th>'
            f'<td style="padding:5px 15px;font-weight:bold;">EUR {metrics["portfolio_net_value"]:,.0f}</td></tr>'
        )

    excl_html = ""
    if excluded_features:
        excl_names = ", ".join(
            f"❌ {ex['name'] if isinstance(ex, dict) else ex}"
            for ex in excluded_features
        )
        excl_html = (
            f'<div style="margin-top:10px;color:{COLORS.neutral};">'
            f"Not selected: {excl_names}</div>"
        )

    return render(
        "portfolio/selection_card.html.j2",
        selected_features=selected_features,
        title=title,
        accent=c,
        metrics_rows=Markup(metrics_rows),
        excl_html=Markup(excl_html),
    )


def optimizer_results_card(
    selected: list[str],
    total_cost: float,
    expected_business_value: float,
    var95: float,
    budget_remaining: float,
    *,
    title: str = "Optimization Results",
    roi: float | None = None,
    net_value: float | None = None,
    cvar95: float | None = None,
    budget_pressure: float | None = None,
    objective: str | None = None,
    accent: str | None = None,
) -> str:
    """Display portfolio optimizer results."""
    c = accent or COLORS.primary

    if roi is None:
        roi = (
            (expected_business_value - total_cost) / total_cost if total_cost > 0 else 0
        )
    if net_value is None:
        net_value = expected_business_value - total_cost
    if cvar95 is None:
        cvar95 = var95
    if budget_pressure is None:
        budget_base = total_cost + budget_remaining
        budget_metric_label = "BUDGET USED"
        budget_metric_value = (
            f"{total_cost / budget_base:.1%}" if budget_base > 0 else "0.0%"
        )
        budget_metric_color = COLORS.secondary
    else:
        budget_metric_label = "BUDGET PRESSURE"
        budget_metric_value = f"{budget_pressure:+.1%}"
        budget_metric_color = COLORS.success if budget_pressure <= 0 else COLORS.danger

    return render(
        "portfolio/optimizer_results_card.html.j2",
        selected=selected,
        total_cost=total_cost,
        budget_remaining=budget_remaining,
        net_value=net_value,
        roi=roi,
        var95=var95,
        cvar95=cvar95,
        budget_metric_label=budget_metric_label,
        budget_metric_value=budget_metric_value,
        budget_metric_color=budget_metric_color,
        objective=objective,
        title=title,
        accent=c,
    )
