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

"""Forecast & LLP (Late Landing Probability) charts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import matplotlib.pyplot as plt
import numpy as np

from ..styling import FIG, HIST_EDGE_COLOR, palette
from ._helpers import (
    _apply_axis_style,
    _cycle_colors,
    _place_bottom_legend,
    _set_xtick_labels,
    _show_fig,
)

ANNUAL_INSTALLMENT_LABEL = "Annual Installment"
BUSINESS_VALUE_EURO_LABEL = "Business Value (€)"
OFFSET_POINTS = "offset points"
FLOOR_BVF_95_LABEL = "Floor (BVF 95%)"

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from fhs.core.model import Feature, SimulationResult


# ── Business Value Forecast ───────────────────────────────────────────


def _deterministic_forecast(feature: Any) -> list[float]:
    """Compute 3-year deterministic forecast from base business value + growth."""
    base = feature.get_base_annual_business_value()
    growth = feature.annual_growth_rate
    return [base * (1 + growth) ** yr for yr in range(3)]


def _installment_schedule(features: list[Any], years: int = 3) -> list[float]:
    """Aggregate annual installment schedule across all features."""
    schedule: list[float] = []
    for year in range(1, years + 1):
        amount = float(
            sum(
                float(getattr(feature, "annual_installment", 0.0))
                for feature in features
                if year <= int(getattr(feature, "installment_years", 1))
            )
        )
        schedule.append(amount)
    return schedule


def plot_business_value_forecast(
    features: list[Any],
    *,
    title: str = "3-Year Business Value Forecast",
    colors: list[str] | None = None,
    show_installment: bool = True,
) -> Figure:
    """Stacked bar + trend line for 3-year business value forecast.

    Parameters
    ----------
    features:
        List of Feature objects with ``.get_base_annual_business_value()`` and
        ``.annual_growth_rate``.
    title:
        Chart title.
    colors:
        Optional list of hex colour strings.
    show_installment:
        Whether to annotate installment costs on the chart.
    """
    feat_colors = _cycle_colors(len(features), colors)
    years = ["Year 1", "Year 2", "Year 3"]
    x = np.arange(3)
    width = 0.5

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=FIG.medium)

    installment = _installment_schedule(features, years=3)

    # ── Left: stacked bars ───────────────────────────────────────────
    bottom = np.zeros(3)
    for i, feature in enumerate(features):
        forecast = _deterministic_forecast(feature)
        ax1.bar(
            x, forecast, width, label=feature.name, bottom=bottom, color=feat_colors[i]
        )
        bottom += forecast

    if show_installment and any(val > 0 for val in installment):
        ax1.step(
            x,
            installment,
            where="mid",
            color=palette["danger"],
            linestyle="--",
            linewidth=2,
            label=ANNUAL_INSTALLMENT_LABEL,
        )

    ax1.set_xlabel("Year", fontsize=12)
    ax1.set_ylabel("Business Value (\u20ac)", fontsize=12)
    ax1.set_title(f"{title} (Stacked)", fontsize=14, fontweight="bold")
    _set_xtick_labels(ax1, list(x), years, rotation=0, fontsize=10)
    _apply_axis_style(ax1, grid_axis="y")
    ax1.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda v, _: f"\u20ac{v / 1000:.0f}k")
    )

    # ── Right: trend lines ───────────────────────────────────────────
    for i, feature in enumerate(features):
        forecast = _deterministic_forecast(feature)
        ax2.plot(
            [1, 2, 3],
            forecast,
            marker="o",
            linewidth=2,
            label=feature.name,
            color=feat_colors[i],
        )

    if show_installment and any(val > 0 for val in installment):
        ax2.step(
            [1, 2, 3],
            installment,
            where="mid",
            color=palette["danger"],
            linestyle="--",
            linewidth=2,
            label=ANNUAL_INSTALLMENT_LABEL,
        )

    ax2.set_xlabel("Year", fontsize=12)
    ax2.set_ylabel("Business Value (\u20ac)", fontsize=12)
    ax2.set_title("Business Value Growth Trend", fontsize=14, fontweight="bold")
    _set_xtick_labels(ax2, [1, 2, 3], years, rotation=0, fontsize=10)
    _apply_axis_style(ax2, grid_axis="y")
    ax2.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda v, _: f"\u20ac{v / 1000:.0f}k")
    )

    # ── Legend centered below both panels ─────────────────────────────
    plt.tight_layout(pad=2.0, w_pad=2.4, rect=(0, 0.02, 1, 0.96))
    h1, l1 = ax1.get_legend_handles_labels()
    legend_bottom = _place_bottom_legend(
        fig,
        h1,
        l1,
        max_cols=4,
        fontsize=8.5,
    )
    fig.subplots_adjust(bottom=max(0.18, legend_bottom))
    _show_fig(fig)
    return fig


def _keur_formatter(v: float, _: Any) -> str:
    return f"€{v / 1000:.0f}k"


def _build_installment_schedules(
    features: list[Any] | None,
    multi_year_results: list[Any],
    n: int,
) -> list[list[float]]:
    if not features or len(features) != n:
        return [[] for _ in range(n)]
    years_count = max((len(myr.years) for myr in multi_year_results), default=3)
    schedules: list[list[float]] = []
    for feat in features:
        dep_per_year = float(getattr(feat, "annual_installment", 0.0))
        dep_years = int(getattr(feat, "installment_years", 1))
        schedules.append(
            [
                dep_per_year if yr <= dep_years else 0.0
                for yr in range(1, years_count + 1)
            ]
        )
    return schedules


# ── Multi-Year Fan Chart ─────────────────────────────────────────────


def plot_multi_year_fan(
    multi_year_results: list[Any],
    *,
    title: str = "3-Year Simulated Business Value",
    colors: list[str] | None = None,
    features: list[Any] | None = None,
) -> Figure:
    """Fan chart with confidence bands per year for multi-year simulations.

    Parameters
    ----------
    multi_year_results:
        List of ``MultiYearResult`` objects (one per feature).
    title:
        Chart title.
    colors:
        Optional list of hex colour strings.
    features:
        Optional list of ``Feature`` objects in the same order as
        ``multi_year_results``. When provided, the annual installment charge
        is drawn as a dashed step line on each feature panel.
    """

    n = len(multi_year_results)
    feat_colors = _cycle_colors(n, colors)

    # Build per-feature installment schedule (one value per simulated year)
    dep_schedules = _build_installment_schedules(features, multi_year_results, n)

    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4.5), squeeze=False)
    fig.suptitle(title, fontsize=14, fontweight="bold")
    axes = axes[0]

    legend_handles: list[Any] = []
    legend_labels: list[str] = []
    dep_line_added = False

    for idx, myr in enumerate(multi_year_results):
        ax = axes[idx]
        yrs = [yr.year for yr in myr.years]
        expected = [yr.expected for yr in myr.years]
        floor = [yr.var_95 for yr in myr.years]
        ceiling = [yr.p95 for yr in myr.years]

        color = feat_colors[idx]
        ax.fill_between(yrs, floor, ceiling, alpha=0.18, color=color)
        ax.fill_between(yrs, floor, expected, alpha=0.10, color=palette["danger"])
        expected_line = ax.plot(
            yrs, expected, marker="o", linewidth=2, color=color, label="Expected"
        )[0]
        floor_line = ax.plot(
            yrs,
            floor,
            linestyle="--",
            linewidth=1,
            color=palette["danger"],
            alpha=0.7,
            label=FLOOR_BVF_95_LABEL,
        )[0]
        ceiling_line = ax.plot(
            yrs,
            ceiling,
            linestyle="--",
            linewidth=1,
            color=palette["secondary"],
            alpha=0.7,
            label="Ceiling (P95)",
        )[0]

        if idx == 0:
            legend_handles = [expected_line, floor_line, ceiling_line]
            legend_labels = ["Expected", FLOOR_BVF_95_LABEL, "Ceiling (P95)"]

        # Installment step line
        schedule = dep_schedules[idx] if dep_schedules[idx] else []
        if schedule and any(val > 0 for val in schedule):
            dep_line = ax.step(
                yrs,
                schedule[: len(yrs)],
                where="mid",
                color=palette["danger"],
                linestyle=":",
                linewidth=2,
                label=ANNUAL_INSTALLMENT_LABEL,
            )[0]
            if not dep_line_added:
                legend_handles.append(dep_line)
                legend_labels.append(ANNUAL_INSTALLMENT_LABEL)
                dep_line_added = True

        ax.set_title(myr.feature_name, fontsize=12, fontweight="bold")
        ax.set_xlabel("Year")
        ax.set_ylabel(BUSINESS_VALUE_EURO_LABEL)
        _set_xtick_labels(ax, yrs, [f"Y{y}" for y in yrs], rotation=0, fontsize=10)
        _apply_axis_style(ax, grid_axis="y")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(_keur_formatter))

    plt.tight_layout(pad=2.0, rect=(0, 0.02, 1, 0.96))
    if legend_handles:
        legend_bottom = _place_bottom_legend(
            fig,
            legend_handles,
            legend_labels,
            max_cols=4,
            fontsize=8.5,
        )
        fig.subplots_adjust(bottom=max(0.14, legend_bottom))
    _show_fig(fig)
    return fig


def _draw_llp_feature(
    ax: Any,
    f: Any,
    result: Any,
    selected: set[str],
) -> None:
    llp = f.likelihood_of_non_delivery
    rev = result.expected_business_value
    cost = f.development_cost

    if llp <= 0.15:
        color = palette["secondary"]
    elif llp <= 0.30:
        color = palette["warning"]
    else:
        color = palette["danger"]

    in_portfolio = f.name in selected
    size = max(cost / 800, 30)

    ax.scatter(
        llp * 100,
        rev / 1000,
        s=size,
        color=color,
        alpha=0.85 if in_portfolio else 0.35,
        edgecolors=color if in_portfolio else palette["neutral"],
        linewidths=2.0 if in_portfolio else 1.0,
        zorder=5 if in_portfolio else 3,
    )

    short_name = f.name.split(": ", 1)[-1] if ": " in f.name else f.name
    ax.annotate(
        short_name,
        xy=(llp * 100, rev / 1000),
        xytext=(6, 8),
        textcoords=OFFSET_POINTS,
        fontsize=8,
        color=palette["neutral"],
        alpha=0.9 if in_portfolio else 0.55,
        fontweight="bold" if in_portfolio else "normal",
        rotation=18,
        clip_on=False,
    )


# ── LLP (Late Landing Probability) Charts ────────────────────────────


def plot_llp_landscape(
    features: list[Feature],
    simulation_results: dict[str, SimulationResult],
    *,
    selected_names: list[str] | None = None,
    title: str = "LLP Landscape — Risk vs. Reward",
) -> Figure:
    """Bubble chart: X = LLP, Y = Expected Business Value, size = development cost.

    Features in the portfolio are filled, excluded features are hollow.
    Colour encodes the LLP risk zone (green/amber/red).
    """
    fig, ax = plt.subplots(figsize=FIG.single)

    selected = set(selected_names or [])

    for f in features:
        result = simulation_results.get(f.name)
        if result is None:
            continue
        _draw_llp_feature(ax, f, result, selected)

    # Risk zone backgrounds
    ax.axvspan(0, 15, alpha=0.06, color=palette["secondary"], zorder=0)
    ax.axvspan(15, 30, alpha=0.06, color=palette["warning"], zorder=0)
    ax.axvspan(
        30,
        max(f.likelihood_of_non_delivery for f in features) * 100 + 5,
        alpha=0.06,
        color=palette["danger"],
        zorder=0,
    )

    ax.set_xlabel("Late Landing Probability — LLP (%)", fontsize=11, labelpad=8)
    ax.set_ylabel("Expected Business Value (EUR k)", fontsize=11, labelpad=8)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=14)
    _apply_axis_style(ax, grid_axis="both")
    ax.margins(x=0.08, y=0.12)

    # Zone legend — below the chart to avoid covering data points
    from matplotlib.patches import Patch

    zone_handles = [
        Patch(facecolor=palette["secondary"], alpha=0.45, label="Low (\u2264 15%)"),
        Patch(facecolor=palette["warning"], alpha=0.45, label="Medium (16\u201330%)"),
        Patch(facecolor=palette["danger"], alpha=0.45, label="High (> 30%)"),
    ]
    legend_bottom = _place_bottom_legend(
        fig,
        zone_handles,
        [str(handle.get_label()) for handle in zone_handles],
        max_cols=3,
        title="LLP Zone",
        fontsize=9.0,
    )
    plt.tight_layout(rect=(0, 0.16, 1, 0.96))
    fig.subplots_adjust(bottom=max(0.34, legend_bottom + 0.08))
    _show_fig(fig)
    return fig


def plot_llp_impact_bars(
    delivery_risk_result: dict[str, Any],
    _level_1: dict[str, Any],
    *,
    title: str = "Business Value Impact of Late Landing Probability",
) -> Figure:
    """Horizontal bars showing per-feature business value kept vs. lost due to LLP.

    Each feature is a row. The green portion is business value retained (after LLP gate),
    the red portion is business value eroded by delivery risk.
    """
    features = delivery_risk_result.get("features", [])
    if not features:
        fig, ax = plt.subplots(figsize=(8, 2))
        ax.text(0.5, 0.5, "No feature data", ha="center", va="center")
        _show_fig(fig)
        return fig

    names = []
    retained = []
    eroded = []
    llps = []

    for feat in features:
        name = feat["name"]
        short = name.split(": ", 1)[-1] if ": " in name else name
        llp = feat["non_delivery_risk"]
        delivered_pct = feat["delivered_pct"]

        names.append(short)
        llps.append(llp)
        retained.append(delivered_pct * 100)
        eroded.append((1 - delivered_pct) * 100)

    # Sort by LLP descending (riskiest at top)
    order = sorted(range(len(llps)), key=lambda i: llps[i], reverse=True)
    names = [names[i] for i in order]
    retained = [retained[i] for i in order]
    eroded = [eroded[i] for i in order]
    llps = [llps[i] for i in order]

    fig_height = max(3.5, len(names) * 0.45 + 1.5)
    fig, ax = plt.subplots(figsize=(11, fig_height))

    y = np.arange(len(names))

    ax.barh(
        y,
        retained,
        color=palette["secondary"],
        height=0.55,
        label="Business value retained",
        edgecolor=HIST_EDGE_COLOR,
        linewidth=0.5,
    )
    ax.barh(
        y,
        eroded,
        left=retained,
        color=palette["danger"],
        height=0.55,
        alpha=0.7,
        label="Business value at risk (LLP)",
        edgecolor=HIST_EDGE_COLOR,
        linewidth=0.5,
    )

    # LLP labels on the right
    for i, (llp_val, _ret, _erd) in enumerate(
        zip(llps, retained, eroded, strict=False)
    ):
        if llp_val > 0.3:
            label_color = palette["danger"]
        elif llp_val > 0.15:
            label_color = palette["warning"]
        else:
            label_color = palette["secondary"]
        ax.text(
            101.5,
            i,
            f"LLP {llp_val * 100:.0f}%",
            va="center",
            ha="left",
            fontsize=9,
            fontweight="bold",
            color=label_color,
        )

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlabel("Business Value Delivery Rate (%)", fontsize=11, labelpad=12)
    ax.set_xlim(0, 115)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=14)
    _apply_axis_style(ax, grid_axis="x")
    ax.invert_yaxis()

    # Legend below the chart
    handles, labels = ax.get_legend_handles_labels()
    plt.tight_layout(rect=(0, 0.10, 1, 0.97))
    legend_bottom = _place_bottom_legend(
        fig,
        handles,
        labels,
        max_cols=2,
        fontsize=9.0,
    )
    fig.subplots_adjust(bottom=max(0.26, legend_bottom + 0.03))
    _show_fig(fig)
    return fig
