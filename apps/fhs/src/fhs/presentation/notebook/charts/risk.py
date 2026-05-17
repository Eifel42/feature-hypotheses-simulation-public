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

"""Risk comparison, stress test, waterfall, and budget risk layer charts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, cast

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from ..styling import (
    FIG,
    HIST_BINS,
    HIST_EDGE_COLOR,
    HIST_EDGE_WIDTH,
    palette,
)
from ._helpers import (
    _apply_axis_style,
    _cycle_colors,
    _place_bottom_legend,
    _set_xtick_labels,
    _show_fig,
)

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from fhs.core.model.value_objects.risk_layer_stats import WaterfallSummary
    from fhs.core.model.value_objects.sprint_delivery import (
        DeliverySimulationResult,
        PortfolioProfitabilityResult,
    )


AFTER_DELIVERY_LABEL = "After Delivery"
AFTER_DEVELOPMENT_LABEL = "After Development"


# ── Risk Comparison (overlay + ranking bars) ──────────────────────────


def plot_risk_comparison(
    features: dict[str, dict[str, Any]],
    *,
    title: str = "Risk Comparison",
    unit: str = "EUR k",
    divisor: float = 1_000.0,
    colors: dict[str, str] | None = None,
) -> Figure:
    """Two-panel chart: overlaid histograms (left) + expected-vs-floor bar chart (right).

    Parameters
    ----------
    features:
        Same schema as :func:`plot_feature_distributions`.
    title:
        Chart title.
    unit:
        Display unit label (e.g. "EUR k").
    divisor:
        Divisor applied to monetary values for display.
    colors:
        Optional mapping of feature label to hex colour string.
    """
    labels = list(features.keys())
    default_colors = _cycle_colors(len(labels))
    feat_colors = colors or {lbl: default_colors[i] for i, lbl in enumerate(labels)}

    fig, (ax_dist, ax_rank) = plt.subplots(1, 2, figsize=FIG.medium)
    fig.suptitle(title, fontsize=16, fontweight="bold", y=0.995)

    # ── Left: overlaid histograms ────────────────────────────────────
    for label in labels:
        d = features[label]
        ax_dist.hist(
            d["scenarios"] / divisor,
            bins=HIST_BINS,
            alpha=0.40,
            color=feat_colors[label],
            label=d.get("name", label),
            edgecolor=HIST_EDGE_COLOR,
            linewidth=HIST_EDGE_WIDTH,
        )
        ax_dist.axvline(
            d["expected"] / divisor,
            color=feat_colors[label],
            linewidth=1.5,
            linestyle="-",
        )

    ax_dist.set_xlabel(f"Annual Value ({unit})", labelpad=8)
    ax_dist.set_ylabel("Scenarios", labelpad=8)
    ax_dist.set_title("Business Value Distributions", pad=12)
    _apply_axis_style(ax_dist, grid_axis="y")

    # ── Right: expected vs VaR horizontal bars ───────────────────────
    y_pos = np.arange(len(labels))
    expected_vals = [features[lbl]["expected"] / divisor for lbl in labels]
    var_vals = [features[lbl]["var95"] / divisor for lbl in labels]
    bar_cols = [feat_colors[lbl] for lbl in labels]
    f_names = [features[lbl].get("name", lbl) for lbl in labels]

    ax_rank.barh(
        y_pos - 0.18, expected_vals, 0.33, color=bar_cols, alpha=0.9, label="Expected"
    )
    ax_rank.barh(
        y_pos + 0.18,
        var_vals,
        0.33,
        color=bar_cols,
        alpha=0.35,
        label="Business Value Floor 95",
    )
    ax_rank.set_yticks(y_pos)
    ax_rank.set_yticklabels(f_names, fontsize=9)
    ax_rank.set_xlabel(f"Annual Value ({unit})", labelpad=8)
    ax_rank.set_title("Expected vs. Business Value Floor 95", pad=12)
    _apply_axis_style(ax_rank, grid_axis="y")

    for bar, val in zip(
        ax_rank.patches[: len(labels)],
        expected_vals,
        strict=False,
    ):
        ax_rank.text(
            val + max(expected_vals) * 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"\u20ac{val:.0f}k",
            va="center",
            fontsize=9,
            color=palette["neutral"],
            fontweight="bold",
        )
    if expected_vals or var_vals:
        max_axis = max(expected_vals + var_vals)
        ax_rank.set_xlim(0, max_axis * 1.28)

    h1, l1 = ax_dist.get_legend_handles_labels()
    h2, l2 = ax_rank.get_legend_handles_labels()
    plt.tight_layout(pad=2.5, rect=(0, 0.08, 1, 0.90))
    legend_bottom = _place_bottom_legend(
        fig,
        h1 + h2,
        l1 + l2,
        max_cols=4,
        fontsize=9.0,
    )
    fig.subplots_adjust(bottom=max(0.20, legend_bottom + 0.01), top=0.86)
    _show_fig(fig)
    return fig


# ── Stress Test ───────────────────────────────────────────────────────


def plot_risk_layer_decay(
    waterfall: WaterfallSummary,
    *,
    title: str = "Portfolio Expected Business Value Decay Across Risk Layers",
    annual_installment: float | None = None,
) -> Figure:
    """Line chart showing expected business value after each portfolio risk layer."""
    layer_names = [
        row.layer.replace(" (no risk)", "")
        .replace(" (all risks)", "")
        .replace(AFTER_DELIVERY_LABEL, AFTER_DEVELOPMENT_LABEL)
        for row in waterfall.rows
    ]
    expected_vals = [row.expected for row in waterfall.rows]

    fig, ax = plt.subplots(figsize=FIG.single)
    x = list(range(len(layer_names)))
    expected_k = [value / 1000.0 for value in expected_vals]

    ax.plot(
        x,
        expected_k,
        marker="o",
        linewidth=3,
        color=palette["primary"],
        label="Expected business value",
        markersize=10,
    )

    offset = max(expected_k) * 0.03 if expected_k else 0.0
    for x_pos, value in zip(x, expected_k, strict=False):
        ax.text(
            x_pos,
            value + offset,
            f"EUR {value:.0f}k",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color=palette["neutral"],
        )

    _set_xtick_labels(ax, x, layer_names, rotation=0)
    ax.set_ylabel("Business Value (EUR thousands)", labelpad=8)
    ax.set_title(title, pad=12, fontweight="bold")
    _apply_axis_style(ax, grid_axis="y")

    if annual_installment is not None and annual_installment > 0:
        dep_k = annual_installment / 1000.0
        ax.axhline(
            dep_k,
            color=palette["danger"],
            linestyle="--",
            linewidth=1.6,
            label=f"Annual Installment (EUR {dep_k:.0f}k)",
        )

    ax.legend(loc="best", fontsize=10)

    plt.tight_layout(pad=1.5)
    _show_fig(fig)
    return fig


def plot_sensitivity_curve(
    results: dict[float, Any],
    *,
    param_name: str,
    title: str | None = None,
    color: str | None = None,
    annual_installment: float | None = None,
) -> Figure:
    """Line chart showing expected portfolio business value across sensitivity levels."""
    ordered_levels = sorted(results.keys())
    x_values = [level * 100 for level in ordered_levels]
    y_values = [
        results[level].after_risk_3.expected / 1000.0 for level in ordered_levels
    ]

    fig, ax = plt.subplots(figsize=FIG.single)
    line_color = color or palette["primary"]

    ax.plot(
        x_values,
        y_values,
        marker="o",
        linewidth=2.8,
        color=line_color,
        markersize=9,
        label="Expected business value",
    )

    offset = max(y_values) * 0.03 if y_values else 0.0
    for x_pos, value in zip(x_values, y_values, strict=False):
        ax.text(
            x_pos,
            value + offset,
            f"EUR {value:.0f}k",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color=palette["neutral"],
        )

    ax.set_xlabel(f"{param_name} (%)", labelpad=8)
    ax.set_ylabel("Expected portfolio business value (EUR thousands)", labelpad=8)
    ax.set_title(
        title or f"{param_name} -> Expected Business Value",
        pad=12,
        fontweight="bold",
    )
    _apply_axis_style(ax, grid_axis="y")

    if annual_installment is not None and annual_installment > 0:
        dep_k = annual_installment / 1000.0
        ax.axhline(
            dep_k,
            color=palette["danger"],
            linestyle="--",
            linewidth=1.6,
            label=f"Annual Installment (EUR {dep_k:.0f}k)",
        )

    ax.legend(loc="best", fontsize=10)

    plt.tight_layout(pad=1.5)
    _show_fig(fig)
    return fig


# ── Sensitivity Panel (combined) ──────────────────────────────────────


def plot_sensitivity_panel(
    panels: list[tuple[dict[float, Any], str, str]],
    *,
    title: str = "Risk Sensitivity — Expected Portfolio Business Value",
    annual_installment: float | None = None,
) -> Figure:
    """Side-by-side sensitivity curves for multiple risk factors.

    Args:
        panels: List of ``(results_dict, param_name, color)`` tuples.
        title: Overall figure title.
        annual_installment: Optional installment reference line.
    """
    n = len(panels)
    fig, axes = plt.subplots(
        1,
        n,
        figsize=(FIG.single[0], FIG.single[1]),
        sharey=True,
    )
    if n == 1:
        axes = [axes]

    for _idx, (ax, (results, param_name, color)) in enumerate(
        zip(axes, panels, strict=False)
    ):
        ordered = sorted(results.keys())
        x = [level * 100 for level in ordered]
        y = [results[level].after_risk_3.expected / 1000.0 for level in ordered]

        ax.plot(x, y, marker="o", linewidth=2.8, color=color, markersize=9)

        offset = max(y) * 0.03 if y else 0.0
        for xp, val in zip(x, y, strict=False):
            ax.text(
                xp,
                val + offset,
                f"EUR {val:.0f}k",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
                color=palette["neutral"],
            )

        ax.set_xlabel(f"{param_name} (%)", labelpad=8)
        ax.set_title(param_name, fontweight="bold", pad=10)
        _apply_axis_style(ax, grid_axis="y")

        if annual_installment is not None and annual_installment > 0:
            dep_k = annual_installment / 1000.0
            ax.axhline(
                dep_k,
                color=palette["danger"],
                linestyle="--",
                linewidth=1.6,
                label=f"Installment (EUR {dep_k:.0f}k)",
            )

    axes[0].set_ylabel("Expected Business Value (EUR thousands)", labelpad=8)

    fig.suptitle(title, fontweight="bold", fontsize=13)
    plt.tight_layout(rect=(0, 0, 1, 0.95))
    _show_fig(fig)
    return fig


# ── Feature Risk Layer Decay ───────────────────────────────────────────


def plot_feature_risk_layer_decay(
    feature_names: list[str],
    expected_matrix: list[list[float]],
    layer_labels: list[str] | None = None,
    *,
    title: str = "Feature Expected Business Value Decay Across Risk Layers",
) -> Figure:
    """Line chart: expected business value per feature across risk layers.

    Args:
        feature_names: Short display names, one per line.
        expected_matrix: Shape [n_features][n_layers], values in EUR.
        layer_labels: X-axis labels (defaults to Base → After Global).
        title: Chart title.
    """
    labels = layer_labels or [
        "Base",
        AFTER_DEVELOPMENT_LABEL,
        "After Market",
        "After Component",
        "After Global",
    ]
    x = list(range(len(labels)))
    colors = _cycle_colors(len(feature_names))

    fig, ax = plt.subplots(figsize=FIG.single)

    for idx, (name, color) in enumerate(zip(feature_names, colors, strict=False)):
        y_k = [v / 1000.0 for v in expected_matrix[idx]]
        ax.plot(
            x, y_k, marker="o", linewidth=2.5, label=name, color=color, markersize=8
        )

    _set_xtick_labels(ax, x, labels, rotation=0)
    ax.set_ylabel("Expected Business Value (EUR thousands)", labelpad=8)
    ax.set_title(title, pad=12, fontweight="bold")
    _apply_axis_style(ax, grid_axis="y")
    ax.legend(loc="best", fontsize=10)

    plt.tight_layout(pad=1.5)
    _show_fig(fig)
    return fig


def plot_feature_risk_decay(
    feature_names: list[str],
    expected_matrix: list[list[float]],
    layer_labels: list[str] | None = None,
    *,
    title: str = "Feature Business Value Retention Across Risk Layers",
) -> Figure:
    """Retention-% decay chart with green / yellow / red background bands.

    Unlike :func:`plot_feature_risk_layer_decay` (EUR y-axis), this chart
    normalises each feature to 100 % at the Base layer so that
    traffic-light threshold bands apply across all features regardless of
    their absolute business value.

    Green band: retention > 60 %  |  Yellow: 30–60 %  |  Red: < 30 %

    Args:
        feature_names: Short display names, one per line.
        expected_matrix: Shape [n_features][n_layers], values in EUR.
        layer_labels: X-axis labels (defaults to Base → After Global).
        title: Chart title.
    """
    labels = layer_labels or [
        "Base",
        AFTER_DEVELOPMENT_LABEL,
        "After Market",
        "After Component",
        "After Global",
    ]
    x = list(range(len(labels)))
    colors = _cycle_colors(len(feature_names))

    fig, ax = plt.subplots(figsize=FIG.single)

    # Traffic-light background bands (retention %)
    ax.axhspan(0, 30, alpha=0.08, color=palette["danger"], zorder=0)
    ax.axhspan(30, 60, alpha=0.08, color=palette["warning"], zorder=0)
    ax.axhspan(60, 100, alpha=0.06, color=palette["secondary"], zorder=0)

    # Threshold reference lines
    ax.axhline(60, color=palette["secondary"], linewidth=0.8, linestyle="--", alpha=0.5)
    ax.axhline(30, color=palette["danger"], linewidth=0.8, linestyle="--", alpha=0.5)

    for idx, (name, color) in enumerate(zip(feature_names, colors, strict=False)):
        base = expected_matrix[idx][0] if expected_matrix[idx] else 0.0
        if base <= 0:
            continue
        y_pct = [100.0 * v / base for v in expected_matrix[idx]]
        ax.plot(
            x, y_pct, marker="o", linewidth=2.5, label=name, color=color, markersize=8
        )
        # Annotate final retention percentage
        ax.annotate(
            f"{y_pct[-1]:.0f}%",
            (x[-1], y_pct[-1]),
            textcoords="offset points",
            xytext=(7, 0),
            fontsize=9,
            fontweight="bold",
            color=color,
            va="center",
        )

    _set_xtick_labels(ax, x, labels, rotation=0)
    ax.set_ylabel("Business Value Retention (%)", labelpad=8)
    ax.set_ylim(0, 110)
    ax.set_title(title, pad=12, fontweight="bold")
    _apply_axis_style(ax, grid_axis="y")
    handles, labels = ax.get_legend_handles_labels()
    plt.tight_layout(pad=1.5, rect=(0, 0.08, 1, 0.95))
    legend_bottom = _place_bottom_legend(
        fig,
        handles,
        labels,
        max_cols=min(4, max(1, len(labels))),
        fontsize=9.0,
    )
    fig.subplots_adjust(bottom=max(0.26, legend_bottom + 0.02), top=0.90)
    _show_fig(fig)
    return fig


def plot_sprint_delay_grid(
    delivery_results: dict[str, DeliverySimulationResult],
    *,
    title: str = "Delay Simulation — Actual vs Planned Sprints",
) -> Figure:
    """Histogram grid comparing planned and simulated actual sprints per feature."""
    ordered_names = sorted(delivery_results)
    fig, axes = plt.subplots(
        1, len(ordered_names), figsize=(5 * len(ordered_names), 4), sharey=True
    )

    if not hasattr(axes, "__len__"):
        axes = [axes]

    legend_handles = []
    legend_labels = []

    for idx, (ax, name) in enumerate(zip(axes, ordered_names, strict=False)):
        result = delivery_results[name]
        bins = range(1, result.max_actual_sprints + 2)
        ax.hist(
            result.actual_sprints,
            bins=bins,
            alpha=0.85,
            color=palette["primary"],
            edgecolor=HIST_EDGE_COLOR,
        )
        planned_line = ax.axvline(
            result.planned_sprints,
            color=palette["danger"],
            linestyle="--",
            linewidth=2,
            label="Planned",
        )
        ax.set_title(name.split(": ", 1)[-1], fontsize=10, fontweight="bold")
        ax.set_xlabel("Actual sprints")
        if idx == 0:
            ax.set_ylabel("Scenarios")
            legend_handles = [planned_line]
            legend_labels = ["Planned"]
        _apply_axis_style(ax, grid_axis="y")

    # Keep clear headroom so the figure title does not overlap subplot titles
    # (e.g., long feature names like "Traceability").
    fig.suptitle(title, fontsize=13, fontweight="bold", y=0.96)
    plt.tight_layout(rect=(0, 0.08, 1, 0.86))
    if legend_handles:
        legend_bottom = _place_bottom_legend(
            fig,
            legend_handles,
            legend_labels,
            max_cols=1,
            fontsize=9.0,
        )
        fig.subplots_adjust(bottom=max(0.22, legend_bottom + 0.01), top=0.84)
    _show_fig(fig)
    return fig


def plot_cost_comparison(
    delivery_results: dict[str, DeliverySimulationResult],
    *,
    title: str = "Planned vs Simulated Development Burn Cost",
    include_tail_metrics: bool = False,
) -> Figure:
    """Grouped bar chart for development burn cost metrics.

    By default, the chart compares planned vs expected cost. Set
    ``include_tail_metrics=True`` to also display CaR 95% and CVaR 95%, which
    aligns the visual with the notebook risk table.
    """
    ordered_names = sorted(delivery_results)
    x = list(range(len(ordered_names)))
    planned_vals = [
        (
            result.expected_actual_cost / (1.0 + result.cost_uplift)
            if (1.0 + result.cost_uplift) > 0
            else 0.0
        )
        for result in (delivery_results[name] for name in ordered_names)
    ]
    expected_vals = [
        delivery_results[name].expected_actual_cost for name in ordered_names
    ]
    car_vals = [delivery_results[name].cost_p95 for name in ordered_names]
    cvar_vals = [delivery_results[name].cost_cvar for name in ordered_names]

    fig, ax = plt.subplots(figsize=FIG.single)
    if include_tail_metrics:
        width = 0.18
        ax.bar(
            [i - 1.5 * width for i in x],
            planned_vals,
            width=width,
            color=palette["secondary"],
            label="Planned development burn",
        )
        ax.bar(
            [i - 0.5 * width for i in x],
            expected_vals,
            width=width,
            color=palette["warning"],
            label="Expected development burn",
        )
        ax.bar(
            [i + 0.5 * width for i in x],
            car_vals,
            width=width,
            color=palette["primary"],
            label="CaR 95%",
        )
        ax.bar(
            [i + 1.5 * width for i in x],
            cvar_vals,
            width=width,
            color=palette["danger"],
            label="CVaR 95%",
        )
    else:
        width = 0.36
        ax.bar(
            [i - width / 2 for i in x],
            planned_vals,
            width=width,
            color=palette["secondary"],
            label="Planned development burn",
        )
        ax.bar(
            [i + width / 2 for i in x],
            expected_vals,
            width=width,
            color=palette["warning"],
            label="Expected development burn",
        )
    _set_xtick_labels(
        ax,
        x,
        [name.split(": ", 1)[-1] for name in ordered_names],
        rotation=0,
    )
    ax.set_ylabel("Cost (EUR)")
    ax.set_title(title, pad=12, fontweight="bold")
    _apply_axis_style(ax, grid_axis="y")
    ax.legend(loc="best", fontsize=10)

    plt.tight_layout(rect=(0, 0, 1, 0.97))
    _show_fig(fig)
    return fig


def _render_heatmap_cell(
    ax: Any,
    row_idx: int,
    col_idx: int,
    value_k: float,
    inv_k: float,
) -> None:
    gap_k = value_k - inv_k
    is_loss = gap_k < 0
    margin_pct = (gap_k / inv_k * 100.0) if inv_k > 0 else 0.0
    status_color = palette["danger"] if is_loss else palette["success"]
    status_label = "Below break-even" if is_loss else "Profit buffer"
    label = (
        f"EUR {value_k:.0f}k\n{gap_k:.0f}k below\n{margin_pct:.0f}% margin"
        if is_loss
        else f"EUR {value_k:.0f}k\n+{gap_k:.0f}k buffer\n+{margin_pct:.0f}% margin"
    )

    # A white information tile keeps labels readable even when the heatmap
    # background is saturated. Colour communicates state through the border,
    # not through low-contrast text-on-fill combinations.
    ax.text(
        col_idx,
        row_idx + 0.04,
        label,
        ha="center",
        va="center",
        fontsize=10.2,
        fontweight="bold",
        color=palette["heatmap_label_text"],
        bbox={
            "boxstyle": "round,pad=0.42,rounding_size=0.12",
            "facecolor": palette["background"],
            "edgecolor": status_color,
            "linewidth": 1.8,
            "alpha": 0.96,
        },
        zorder=5,
    )
    ax.text(
        col_idx,
        row_idx - 0.32,
        status_label.upper(),
        ha="center",
        va="center",
        fontsize=7.5,
        fontweight="bold",
        color=palette["background"],
        bbox={
            "boxstyle": "round,pad=0.26,rounding_size=0.12",
            "facecolor": status_color,
            "edgecolor": status_color,
            "linewidth": 0,
            "alpha": 1.0,
        },
        zorder=6,
    )
    if row_idx == 1 and col_idx == 1:
        ax.add_patch(
            Rectangle(
                (col_idx - 0.5, row_idx - 0.5),
                1,
                1,
                linewidth=5.0,
                edgecolor=palette["heatmap_label_text"],
                facecolor="none",
                linestyle="-",
                zorder=7,
            )
        )
        ax.add_patch(
            Rectangle(
                (col_idx - 0.5, row_idx - 0.5),
                1,
                1,
                linewidth=2.4,
                edgecolor=palette["background"],
                facecolor="none",
                linestyle="--",
                zorder=8,
            )
        )


def plot_delivery_market_resilience(
    heatmap_data: Mapping[tuple[float, float], float],
    *,
    investment: float,
    llp_factors: tuple[float, ...] = (0.5, 1.0, 1.5),
    market_levels: tuple[float, ...] = (0.10, 0.20, 0.30),
    title: str = "Portfolio Resilience: Development Risk x Market Risk",
) -> tuple[Figure, dict[str, float]]:
    """Render delivery-vs-market resilience heatmap and return summary values.

    Args:
        heatmap_data: Mapping of ``(llp_factor, market_probability)`` to EUR values.
        investment: Portfolio investment in EUR used as break-even center.
        llp_factors: Ordered LLP multipliers for heatmap rows.
        market_levels: Ordered market-shock probabilities for heatmap columns.
        title: Figure title.

    Returns:
        Tuple ``(figure, summary)`` where ``summary`` includes:
        ``base_k``, ``improved_k``, ``worsened_k``, ``delivery_gain_k``,
        and ``delivery_loss_stress_k`` in EUR thousands.
    """
    inv_k = investment / 1_000.0
    row_labels = [
        "Better development\n(failure rate halved)",
        "Base case\n(current failure rate)",
        "Worse development\n(failure rate +50%)",
    ]
    col_labels = [f"Market {p:.0%}" for p in market_levels]

    matrix = np.array(
        [
            [
                heatmap_data[(llp_factor, market_level)] / 1_000.0
                for market_level in market_levels
            ]
            for llp_factor in llp_factors
        ]
    )

    margin_matrix = matrix - inv_k

    fig, ax = plt.subplots(figsize=(11.6, 7.0), facecolor=palette["surface"])
    ax.set_facecolor(palette["surface"])
    cmap = LinearSegmentedColormap.from_list(
        "profit_loss_margin",
        [
            palette["heatmap_loss_deep"],
            palette["heatmap_loss_mid"],
            palette["heatmap_loss_soft"],
            palette["heatmap_break_even"],
            palette["heatmap_profit_soft"],
            palette["heatmap_profit_mid"],
            palette["heatmap_profit_deep"],
        ],
        N=256,
    )
    # TwoSlopeNorm requires strictly vmin < vcenter < vmax. Clamp defensively
    # in case the heatmap values lie entirely on one side of the break-even.
    raw_vmin = float(margin_matrix.min()) - 15.0
    raw_vmax = float(margin_matrix.max()) + 15.0
    pad = max(1.0, abs(inv_k) * 0.01)
    vmin = min(raw_vmin, -pad)
    vmax = max(raw_vmax, pad)
    norm = TwoSlopeNorm(vmin=vmin, vcenter=0.0, vmax=vmax)
    heat = ax.imshow(margin_matrix, cmap=cmap, norm=norm, aspect="auto")

    # Subtle separators between cells for dashboard readability.
    ax.set_xticks(np.arange(-0.5, len(col_labels), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(row_labels), 1), minor=True)
    ax.grid(
        which="minor",
        color=palette["background"],
        linestyle="-",
        linewidth=2.2,
        alpha=1.0,
    )
    ax.tick_params(which="minor", bottom=False, left=False)

    for row_idx in range(len(llp_factors)):
        for col_idx in range(len(market_levels)):
            _render_heatmap_cell(
                ax, row_idx, col_idx, float(matrix[row_idx, col_idx]), inv_k
            )

    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, fontsize=11, fontweight="bold")
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=11, fontweight="bold")
    ax.set_xlabel(
        "Market shock probability", fontsize=12, labelpad=12, fontweight="bold"
    )
    ax.set_ylabel(
        "Development risk scenario", fontsize=12, labelpad=12, fontweight="bold"
    )
    ax.set_title(
        title, fontsize=18, fontweight="bold", pad=34, color=palette["neutral"]
    )
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Centered subtitle under the headline; break-even is shown only here.
    ax.text(
        0.5,
        1.03,
        f"Colour shows distance from break-even investment: EUR {inv_k:.0f}k",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=11,
        color=palette["neutral"],
        fontweight="bold",
    )

    cbar = fig.colorbar(heat, ax=ax, fraction=0.045, pad=0.025)
    cbar.ax.tick_params(labelsize=9)
    cbar.set_label(
        "Margin vs. investment (EUR k)", fontsize=10, color=palette["neutral"]
    )

    legend_handles = [
        Line2D(
            [0],
            [0],
            marker="s",
            color="none",
            markerfacecolor=palette["success"],
            markeredgecolor=palette["success"],
            markersize=9,
            label="Profit buffer",
        ),
        Line2D(
            [0],
            [0],
            marker="s",
            color="none",
            markerfacecolor=palette["danger"],
            markeredgecolor=palette["danger"],
            markersize=9,
            label="Below break-even",
        ),
        Line2D(
            [0],
            [0],
            marker="s",
            linestyle="--",
            color=palette["heatmap_label_text"],
            markerfacecolor=palette["background"],
            markeredgecolor=palette["heatmap_label_text"],
            markersize=9,
            label="Base case",
        ),
    ]
    plt.tight_layout(rect=(0.0, 0.06, 1.0, 0.95))
    legend_labels = [cast(str, h.get_label()) for h in legend_handles]
    legend_bottom = _place_bottom_legend(
        fig,
        legend_handles,
        legend_labels,
        max_cols=3,
        title="Legend",
        fontsize=10.0,
    )
    plt.subplots_adjust(bottom=max(0.18, legend_bottom + 0.02), top=0.88)
    _show_fig(fig)

    base_k = heatmap_data[(1.0, 0.20)] / 1_000.0
    improved_k = heatmap_data[(0.5, 0.20)] / 1_000.0
    worsened_k = heatmap_data[(1.5, 0.20)] / 1_000.0
    summary = {
        "base_k": base_k,
        "improved_k": improved_k,
        "worsened_k": worsened_k,
        "delivery_gain_k": improved_k - base_k,
        "delivery_loss_stress_k": base_k - worsened_k,
    }
    return fig, summary


def plot_runtime_comparison(
    runtime_data: dict[str, dict[str, list[float]]],
    *,
    title: str = "Runtime and Floor Quality by Feature Count",
) -> Figure:
    """Two-panel chart for solver runtime and floor quality across feature counts.

    Parameters
    ----------
    runtime_data:
        Mapping per solver with keys ``x``, ``runtime``, and ``floor``.
        Example: ``{"ilp": {"x": [8, 12], "runtime": [...], "floor": [...]}}``.
    title:
        Figure title.
    """
    fig, axes = plt.subplots(1, 2, figsize=FIG.medium)
    fig.suptitle(title, fontsize=14, fontweight="bold", y=0.98)

    method_style = {
        "exact": ("Exact", palette["primary"]),
        "ilp": ("Linear (ILP)", palette["secondary"]),
        "greedy": ("Greedy", palette["danger"]),
    }

    for method in ("exact", "ilp", "greedy"):
        if method not in runtime_data:
            continue
        label, color = method_style[method]
        x_values = runtime_data[method].get("x", [])
        runtime_values = runtime_data[method].get("runtime", [])
        floor_values = runtime_data[method].get("floor", [])
        if not x_values:
            continue

        axes[0].plot(
            x_values,
            runtime_values,
            marker="o",
            linewidth=2.2,
            color=color,
            label=label,
        )
        axes[1].plot(
            x_values,
            [value / 1000.0 for value in floor_values],
            marker="o",
            linewidth=2.2,
            color=color,
            label=label,
        )

    axes[0].set_title("Runtime by Feature Count")
    axes[0].set_xlabel("Number of features")
    axes[0].set_ylabel("Runtime (seconds)")
    _apply_axis_style(axes[0], grid_axis="y")

    axes[1].set_title("Floor Quality by Feature Count")
    axes[1].set_xlabel("Number of features")
    axes[1].set_ylabel("Business Value Floor 95 (EUR k)")
    _apply_axis_style(axes[1], grid_axis="y")

    handles, labels = axes[1].get_legend_handles_labels()
    plt.tight_layout(pad=2.0, rect=(0, 0.02, 1, 0.94))
    if handles:
        legend_bottom = _place_bottom_legend(
            fig,
            handles,
            labels,
            max_cols=min(3, len(labels)),
            fontsize=9.0,
        )
        fig.subplots_adjust(bottom=max(0.16, legend_bottom))

    _show_fig(fig)
    return fig


def plot_stress_test(
    results: list[tuple[str, str, float, float, float, str]],
    *,
    title: str = "Stress Test Results",
    annual_installment: float | None = None,
) -> Figure:
    """Horizontal bars comparing baseline vs. stressed business value per scenario.

    Parameters
    ----------
    results:
        ``[(scenario_key, display_name, baseline_k, stressed_k,
        change_pct, color), ...]``
    title:
        Chart title.
    annual_installment:
        Optional annual cost installment to annotate on the chart.
    """
    fig, ax = plt.subplots(figsize=FIG.single)

    for i, (_key, _name, baseline, stressed, change, color) in enumerate(results):
        ax.barh(
            i,
            baseline,
            0.35,
            color=palette["neutral"],
            alpha=0.50,
            label="Baseline" if i == 0 else "",
        )
        ax.barh(
            i,
            stressed,
            0.35,
            color=color,
            alpha=0.85,
            label="Stressed" if i == 0 else "",
        )
        ax.text(
            max(baseline, stressed) + 2,
            i,
            f"{change:+.1f}%",
            va="center",
            fontweight="bold",
            fontsize=12,
            color=color,
        )

    ax.set_yticks(range(len(results)))
    ax.set_yticklabels([r[1] for r in results])
    ax.set_xlabel("Expected Business Value (EUR k)")
    ax.set_title(title, pad=12, fontweight="bold")
    _apply_axis_style(ax, grid_axis="x")

    if annual_installment is not None and annual_installment > 0:
        dep_k = annual_installment / 1000.0
        ax.axvline(
            dep_k,
            color=palette["danger"],
            linestyle="--",
            linewidth=1.6,
            label=f"Annual Installment (EUR {dep_k:.0f}k)",
        )

    if results:
        max_value = max(max(r[2], r[3]) for r in results)
        ax.set_xlim(0, max_value * 1.22)
    handles, labels = ax.get_legend_handles_labels()
    plt.tight_layout(rect=(0, 0.02, 1, 0.95))
    legend_bottom = _place_bottom_legend(
        fig,
        handles,
        labels,
        max_cols=2,
        fontsize=9.0,
    )
    fig.subplots_adjust(bottom=max(0.12, legend_bottom))
    _show_fig(fig)
    return fig


# ── Risk Waterfall ────────────────────────────────────────────────────


def plot_risk_waterfall(
    level_1: dict[str, Any],
    level_3: dict[str, Any],
    *,
    title: str = "Business Value Erosion: Base Case → Development Risk → Crisis Shock",
) -> Figure:
    """Waterfall chart showing how each risk layer erodes expected value and the value floor.

    Three bars per metric: Base Case (market uncertainty),
    After Development Risk (+ delivery failure), After Crisis Shock (+ external event).
    Connectors show the erosion from one level to the next.
    """
    categories = ["Expected Business Value", "Business Value Floor 95"]
    l1_vals = [level_1["market_expected"], level_1["market_var_95"]]
    l2_vals = [level_1["simulated_expected"], level_1["simulated_var_95"]]
    l3_vals = [level_3["shocked_expected"], level_3["shocked_var_95"]]

    fig, axes = plt.subplots(1, 2, figsize=FIG.medium)

    for idx, (cat, v1, v2, v3) in enumerate(
        zip(categories, l1_vals, l2_vals, l3_vals, strict=False)
    ):
        ax = axes[idx]
        labels = ["Base Case", "After Development Risk", "After Crisis Shock"]
        vals = [v1, v2, v3]
        colors = [palette["primary"], palette["accent"], palette["danger"]]

        bars = ax.bar(
            labels,
            vals,
            color=colors,
            width=0.55,
            edgecolor=HIST_EDGE_COLOR,
            linewidth=1.5,
        )

        # Erosion connectors
        for i in range(len(vals) - 1):
            drop = vals[i] - vals[i + 1]
            pct = (drop / vals[i] * 100) if vals[i] > 0 else 0
            mid_x = i + 0.5
            mid_y = (vals[i] + vals[i + 1]) / 2
            ax.annotate(
                f"−{pct:.1f}%",
                xy=(mid_x, mid_y),
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
                color=palette["danger"],
                bbox={
                    "boxstyle": "round,pad=0.3",
                    "fc": palette["background"],
                    "ec": palette["danger"],
                    "alpha": 0.9,
                    "lw": 1,
                },
            )
            # Connector line
            ax.plot(
                [i + 0.28, i + 0.72],
                [vals[i], vals[i + 1]],
                color=palette["danger"],
                linewidth=1.5,
                linestyle="--",
                alpha=0.6,
            )

        # Value labels on bars
        for bar, val in zip(bars, vals, strict=False):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(vals) * 0.015,
                f"€{val / 1000:,.0f}k",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
                color=palette["neutral"],
            )

        ax.set_title(cat, fontsize=13, fontweight="bold", pad=12)
        ax.set_ylim(0, max(vals) * 1.18)
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda v, _: f"€{v / 1000:.0f}k")
        )
        _apply_axis_style(ax, grid_axis="y")

    fig.suptitle(title, fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout(pad=2.0, w_pad=3.0, rect=(0, 0.08, 1, 0.94))
    _show_fig(fig)
    return fig


# ── Budget Risk Layers ───────────────────────────────────────────────


def _solver_level_points(
    budget_results: dict[float, dict[str, Any]],
    ordered_budgets: list[float],
    solver_name: str,
    metric_key: str,
) -> tuple[list[float], list[float]]:
    x_values: list[float] = []
    y_values: list[float] = []
    for budget in ordered_budgets:
        solver_data = budget_results.get(budget, {}).get(solver_name)
        if not solver_data:
            continue
        source = (
            solver_data["l1"] if metric_key != "shocked_var_95" else solver_data["l3"]
        )
        if metric_key not in source:
            continue
        x_values.append(budget / 1000)
        y_values.append(source[metric_key] / 1000)
    return x_values, y_values


def _draw_budget_solver_subplot(
    ax: Any,
    solver_name: str,
    solver_labels: dict[str, str],
    budget_results: dict[float, dict[str, Any]],
    ordered_budgets: list[float],
    annual_installment: float | None,
    level_specs: list[tuple[str, str, str, str]],
) -> None:
    has_data = False

    for metric_key, label, color, marker in level_specs:
        x_values, y_values = _solver_level_points(
            budget_results, ordered_budgets, solver_name, metric_key
        )
        if not x_values:
            continue

        has_data = True
        ax.plot(
            x_values,
            y_values,
            marker=marker,
            linewidth=2.2,
            markersize=6,
            color=color,
            label=label,
        )

    ax.set_title(
        f"{solver_labels.get(solver_name, solver_name.title())} Solver",
        fontsize=12,
        fontweight="bold",
    )
    ax.set_xlabel("Budget (EUR k)", fontsize=10)
    _apply_axis_style(ax, grid_axis="y")

    if annual_installment is not None and annual_installment > 0:
        dep_k = annual_installment / 1000.0
        ax.axhline(
            dep_k,
            color=palette["danger"],
            linestyle="--",
            linewidth=1.4,
            label="Annual Installment" if not has_data else "_nolegend_",
        )

    if has_data:
        ticks = [budget / 1000 for budget in ordered_budgets]
        labels = [f"{budget / 1000:.0f}k" for budget in ordered_budgets]
        _set_xtick_labels(ax, ticks, labels, rotation=24, fontsize=9.5)
    else:
        ax.text(
            0.5,
            0.5,
            "No portfolio selected",
            transform=ax.transAxes,
            ha="center",
            va="center",
            color=palette["neutral"],
        )


def plot_budget_risk_layers(
    budget_results: dict[float, dict[str, Any]],
    *,
    budgets: list[float] | None = None,
    title: str = "Budget Business Value Floor by Solver",
    annual_installment: float | None = None,
) -> Figure:
    """Plot how the business value floor changes across sample budgets.

    Each subplot shows one solver. Within a subplot, three lines compare
    Level 1 (market), Level 2 (+ delivery), and Level 3 (+ shock)
    Business Value Floor 95
    across the given sample budgets.
    """

    ordered_budgets = sorted(budgets or budget_results.keys())
    solver_names = ["exact", "ilp"]
    solver_labels = {"exact": "Exact", "ilp": "ILP"}
    fig, axes = plt.subplots(1, len(solver_names), figsize=FIG.medium, sharey=True)

    if not hasattr(axes, "__len__"):
        axes = [axes]

    level_specs = [
        ("market_var_95", "L1 Market", palette["primary"], "o"),
        ("simulated_var_95", "L2 Delivery", palette["accent"], "s"),
        ("shocked_var_95", "L3 Shock", palette["danger"], "^"),
    ]

    for ax, solver_name in zip(axes, solver_names, strict=False):
        _draw_budget_solver_subplot(
            ax,
            solver_name,
            solver_labels,
            budget_results,
            ordered_budgets,
            annual_installment,
            level_specs,
        )

    axes[0].set_ylabel("Business Value Floor 95 (EUR k)", fontsize=10)
    fig.suptitle(title, fontsize=14, fontweight="bold", y=0.98)
    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        legend_bottom = _place_bottom_legend(
            fig,
            handles,
            labels,
            max_cols=3,
            fontsize=9.0,
        )
    else:
        legend_bottom = 0.0
    plt.tight_layout(pad=2.0, w_pad=2.5, rect=(0, 0.02, 1, 0.94))
    fig.subplots_adjust(bottom=max(0.16, legend_bottom))
    _show_fig(fig)
    return fig


# ── Profit Histogram ─────────────────────────────────────────────────


def plot_profit_histogram(
    profitability: PortfolioProfitabilityResult,
    *,
    title: str = "Portfolio Profit Distribution (Business Value after risk \u2212 Simulated cost)",
) -> Figure:
    """Histogram of portfolio profit scenarios with P5 and mean reference lines.

    Parameters
    ----------
    profitability:
        Result from :meth:`DeliveryAnalysisOperations.profitability`.
    title:
        Chart title.
    """
    fig, ax = plt.subplots(figsize=FIG.single)
    ax.hist(
        profitability.portfolio_profit,
        bins=HIST_BINS,
        color=palette["primary"],
        alpha=0.65,
        edgecolor=HIST_EDGE_COLOR,
        linewidth=HIST_EDGE_WIDTH,
    )
    p5 = profitability.portfolio_profit_p5
    ax.axvline(
        p5,
        color=palette["danger"],
        linestyle="--",
        linewidth=2,
        label=f"5th percentile (EUR {p5:,.0f})",
    )
    mean_profit = profitability.expected_portfolio_profit
    ax.axvline(
        mean_profit,
        color=palette["secondary"],
        linewidth=2,
        label=f"Mean (EUR {mean_profit:,.0f})",
    )
    ax.set_title(title, pad=12, fontweight="bold")
    ax.set_xlabel("Profit (EUR)")
    ax.set_ylabel("Scenarios")
    _apply_axis_style(ax, grid_axis="y")
    ax.legend(loc="best", fontsize=10)

    plt.tight_layout(rect=(0, 0, 1, 0.97))
    _show_fig(fig)
    return fig
