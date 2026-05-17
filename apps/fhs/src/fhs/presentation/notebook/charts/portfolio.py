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

"""Portfolio charts: opportunity cost, feature ranking, business value concentration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from ..styling import FIG, HIST_EDGE_COLOR, palette
from ._helpers import (
    _apply_axis_style,
    _best_text_color,
    _cycle_colors,
    _place_bottom_legend,
    _set_xtick_labels,
    _show_fig,
)

if TYPE_CHECKING:
    from matplotlib.figure import Figure


# ── Opportunity Cost ──────────────────────────────────────────────────


def plot_opportunity_cost(
    costs: list[tuple[str, float]],
    *,
    title: str = "What You Lose By Skipping Each Feature",
) -> Figure:
    """Horizontal bar chart of opportunity costs per feature.

    Parameters
    ----------
    costs:
        ``[(feature_name, cost_eur), ...]`` sorted by preference.
    title:
        Chart title.
    """
    names = [c[0] for c in costs]
    values = [c[1] for c in costs]
    colors = []
    for v in values:
        if v > 100_000:
            colors.append(palette["danger"])
        elif v > 20_000:
            colors.append(palette["warning"])
        else:
            colors.append(palette["secondary"])

    fig, ax = plt.subplots(figsize=FIG.single)
    bars = ax.barh(
        names,
        [v / 1000 for v in values],
        color=colors,
        edgecolor=HIST_EDGE_COLOR,
        height=0.5,
    )
    for bar, v in zip(bars, values, strict=False):
        ax.text(
            bar.get_width() + 0.5,
            bar.get_y() + bar.get_height() / 2,
            f"EUR {v:,.0f}",
            va="center",
            fontweight="bold",
            fontsize=11,
            color=palette["neutral"],
        )
    ax.set_xlabel("Opportunity Cost (EUR k)")
    ax.set_title(title, pad=12, fontweight="bold")
    _apply_axis_style(ax, grid_axis="x")
    ax.invert_yaxis()
    if values:
        max_val_k = max(values) / 1000
        ax.set_xlim(0, max_val_k * 1.20)
    plt.tight_layout(pad=2.0)
    _show_fig(fig)
    return fig


# ── Feature Ranking ───────────────────────────────────────────────────


def plot_feature_ranking(
    rankings: list[dict[str, Any]],
    *,
    title: str = "Feature Ranking: Business Value and Downside View",
    installment_by_feature: dict[str, float] | None = None,
) -> Figure:
    """Grouped bar chart comparing expected business value vs. the downside floor.

    Parameters
    ----------
    rankings:
        List of dicts with keys ``feature``, ``expected_business_value``,
        ``var_95_business_value``, ``risk_ratio``.
    title:
        Chart title.
    installment_by_feature:
        Optional mapping of feature name to annual cost installment for annotation.
    """
    names = [r["feature"] for r in rankings]
    business_values_k = [r["expected_business_value"] / 1000 for r in rankings]
    var_k = [r["var_95_business_value"] / 1000 for r in rankings]
    risks = [r["risk_ratio"] * 100 for r in rankings]

    n = len(names)
    x = np.arange(n)
    width = 0.35

    # Wider figure for many features
    fig_width = max(FIG.single[0], n * 1.3 + 2)
    fig, ax = plt.subplots(figsize=(fig_width, FIG.single[1]))
    ax.bar(
        x - width / 2,
        business_values_k,
        width,
        label="Expected Business Value (EUR k)",
        color=palette["info"],
        edgecolor=HIST_EDGE_COLOR,
    )
    ax.bar(
        x + width / 2,
        var_k,
        width,
        label="Business Value Floor 95 (EUR k)",
        color=palette["danger"],
        edgecolor=HIST_EDGE_COLOR,
    )

    if installment_by_feature:
        dep_k = [installment_by_feature.get(name, 0.0) / 1000.0 for name in names]
        if any(val > 0 for val in dep_k):
            ax.plot(
                x,
                dep_k,
                color=palette["danger"],
                linestyle="--",
                linewidth=2,
                marker="D",
                markersize=5,
                label="Annual Installment (EUR k)",
            )

    badge_fontsize = 9 if n > 6 else 10
    for i, (business_value, var, risk) in enumerate(
        zip(business_values_k, var_k, risks, strict=False)
    ):
        if risk < 20:
            icon = "\u2714"
        elif risk < 40:
            icon = "\u26a0"
        else:
            icon = "\u2716"
        ax.text(
            i,
            max(business_value, var) + max(business_values_k) * 0.03,
            f"{icon} {risk:.0f}%",
            ha="center",
            fontsize=badge_fontsize,
            fontweight="bold",
            color=palette["neutral"],
        )

    label_fontsize = 9 if n > 6 else 11
    rotation = 28 if n > 4 else 0
    _set_xtick_labels(ax, list(x), names, rotation=rotation, fontsize=label_fontsize)
    ax.set_ylabel("EUR (thousands)")
    ax.set_title(title, pad=12)
    _apply_axis_style(ax, grid_axis="y")
    if business_values_k or var_k:
        y_top = max(business_values_k + var_k) * 1.20
        ax.set_ylim(0, y_top)

    # ── Legend centered below x-axis ──────────────────────────────────
    # Rotated x-labels (28°) need extra bottom space to avoid overlapping the legend.
    base_bottom = 0.30 if rotation else 0.22
    plt.tight_layout(pad=2.0, rect=(0, 0.12, 1, 0.96))
    handles, labels = ax.get_legend_handles_labels()
    legend_bottom = _place_bottom_legend(
        fig,
        handles,
        labels,
        max_cols=2,
        fontsize=9.0,
    )
    fig.subplots_adjust(bottom=max(base_bottom, legend_bottom + 0.04))
    _show_fig(fig)
    return fig


# ── Business Value Concentration ──────────────────────────────────────


def plot_business_value_concentration(
    concentration: dict[str, Any],
    *,
    title_prefix: str = "Business Value Concentration",
) -> Figure:
    """Stacked horizontal bar showing business value share per feature + HHI badge.

    Parameters
    ----------
    concentration:
        Output of ``PortfolioAdvisor.get_risk_concentration()`` with keys
        ``concentration``, ``hhi``, ``is_concentrated``.
    title_prefix:
        Prefix for the chart title.
    """
    shares = list(concentration["concentration"].values())
    names = list(concentration["concentration"].keys())
    colors = _cycle_colors(len(names))
    hhi = concentration["hhi"]
    verdict = (
        "Well Diversified" if not concentration["is_concentrated"] else "Concentrated"
    )
    hhi_col = (
        palette["secondary"]
        if not concentration["is_concentrated"]
        else palette["danger"]
    )

    fig, ax = plt.subplots(figsize=(10.8, 3.8))
    left = 0.0
    legend_handles: list[Patch] = []
    legend_labels: list[str] = []
    for name, share, color in zip(names, shares, colors, strict=False):
        width_pct = share * 100
        ax.barh(
            0,
            width_pct,
            0.55,
            left=left * 100,
            color=color,
            edgecolor=HIST_EDGE_COLOR,
            linewidth=1.5,
        )
        legend_handles.append(Patch(facecolor=color, edgecolor=HIST_EDGE_COLOR))
        legend_labels.append(f"{name} ({share:.0%})")

        # Keep block labels short to preserve readability on narrow segments.
        if share >= 0.08:
            ax.text(
                left * 100 + width_pct / 2,
                0,
                f"{share:.0%}",
                ha="center",
                va="center",
                fontsize=10,
                color=_best_text_color(color),
                fontweight="bold",
                clip_on=False,
            )
        left += share

    ax.set_xlim(0, 100)
    ax.set_yticks([])
    ax.set_xlabel("Business Value Share (%)", labelpad=12)
    ax.spines[["top", "right", "left"]].set_visible(False)
    _apply_axis_style(ax, grid_axis="x")
    ax.set_title(
        f"{title_prefix}   \u00b7   HHI: {hhi:.3f} \u2014 {verdict}",
        color=hhi_col,
        pad=12,
    )
    plt.tight_layout(pad=2.0, rect=(0, 0.16, 1, 0.95))
    legend_bottom = _place_bottom_legend(
        fig,
        legend_handles,
        legend_labels,
        max_cols=3,
        title="Feature Shares",
        fontsize=8.8,
    )
    fig.subplots_adjust(bottom=max(0.32, legend_bottom + 0.08))
    _show_fig(fig)
    return fig


def plot_strategy_category_mix(
    category_cost_rows: list[dict[str, Any]] | list[Any],
    *,
    title: str = "Selected Portfolio Mix by Strategy Category (Cost Share)",
) -> Figure:
    """Donut chart for strategy-category cost shares with contrast-safe labels."""
    labels = [str(row["category"]) for row in category_cost_rows]
    values = [float(row["cost"]) for row in category_cost_rows]
    total_cost = float(sum(values))

    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    colors = _cycle_colors(len(values))
    pie_result = ax.pie(
        values,
        labels=None,
        autopct="%1.0f%%",
        startangle=110,
        colors=colors,
        pctdistance=0.77,
        wedgeprops={
            "width": 0.42,
            "edgecolor": palette["background"],
            "linewidth": 1.2,
        },
    )
    wedges = pie_result[0]
    autotexts = pie_result[2] if len(pie_result) > 2 else []

    for wedge, text in zip(wedges, autotexts, strict=False):
        rgba = np.asarray(wedge.get_facecolor(), dtype=float).ravel()
        r = float(rgba[0])
        g = float(rgba[1])
        b = float(rgba[2])
        hex_color = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
        text.set_color(_best_text_color(hex_color))
        text.set_fontweight("bold")
        text.set_fontsize(10)

    legend_labels = [
        f"{label} ({(value / total_cost):.0%})" if total_cost > 0 else f"{label} (0%)"
        for label, value in zip(labels, values, strict=False)
    ]
    ax.text(
        0,
        0,
        f"EUR {total_cost:,.0f}\nTotal Cost",
        ha="center",
        va="center",
        fontweight="bold",
        fontsize=11,
        color=palette["neutral"],
    )
    ax.set_title(title, pad=14)
    plt.tight_layout(rect=(0, 0.14, 1, 0.98))
    legend_bottom = _place_bottom_legend(
        fig,
        list(wedges),
        legend_labels,
        max_cols=min(3, max(1, len(legend_labels))),
        title="Strategy Category",
        fontsize=9.0,
    )
    fig.subplots_adjust(bottom=max(0.30, legend_bottom + 0.06))
    _show_fig(fig)
    return fig
