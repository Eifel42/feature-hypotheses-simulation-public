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

"""Capital budgeting charts: cashflow comparison and NPV analysis."""

from __future__ import annotations

import math
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors as mcolors
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from ..styling import FIG, palette
from ._helpers import _apply_axis_style, _show_fig

ANNOTATION_TEXTCOORDS = "offset points"
AXES_FRACTION = "axes fraction"
OPTION_A_UPFRONT_LABEL = "Option A — Upfront"
OPTION_B_INSTALLMENT_LABEL = "Option B — Installment"
CALLOUT_BOXSTYLE = "round,pad=0.25"


def _contrast_text_color(fill_color: str) -> str:
    """Choose a readable text colour for text placed on a filled shape."""

    red, green, blue = mcolors.to_rgb(fill_color)

    def _channel_luminance(channel: float) -> float:
        return (
            channel / 12.92
            if channel <= 0.03928
            else ((channel + 0.055) / 1.055) ** 2.4
        )

    luminance = (
        0.2126 * _channel_luminance(red)
        + 0.7152 * _channel_luminance(green)
        + 0.0722 * _channel_luminance(blue)
    )
    contrast_on_white = 1.05 / (luminance + 0.05)
    contrast_on_dark = (luminance + 0.05) / 0.05
    return (
        palette["background"]
        if contrast_on_white >= contrast_on_dark
        else palette["neutral"]
    )


def _npv_value(cashflows: list[float], rate: float) -> float:
    return float(sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows)))


def _sign_changes(left: float, right: float) -> bool:
    return (right < 0 < left) or (left < 0 < right)


def _bisect_rate_root(
    cashflows: list[float],
    left: float,
    right: float,
    f_left: float,
) -> float:
    for _ in range(80):
        mid = 0.5 * (left + right)
        f_mid = _npv_value(cashflows, mid)
        if abs(f_mid) < 1e-9:
            return mid
        if _sign_changes(f_left, f_mid):
            right = mid
        else:
            left, f_left = mid, f_mid
    return 0.5 * (left + right)


def _find_non_negative_irr(cashflows: list[float]) -> float | None:
    low = 0.0
    f_low = _npv_value(cashflows, low)
    if abs(f_low) < 1e-9:
        return 0.0

    high = 0.5
    for _ in range(24):
        f_high = _npv_value(cashflows, high)
        if abs(f_high) < 1e-9:
            return high
        if _sign_changes(f_low, f_high):
            return _bisect_rate_root(cashflows, low, high, f_low)
        high *= 1.8
    return None


def _pct_formatter(v: float, _: Any) -> str:
    return f"{v:.0f}%"


def _eur_compact(v: float) -> str:
    sign = "-" if v < 0 else ""
    amount = abs(v)
    if amount >= 950_000:
        return f"{sign}€{amount / 1_000_000:.1f}m"
    return f"{sign}€{amount / 1_000:.0f}k"


def _eur_readable(v: float) -> str:
    sign = "−" if v < 0 else ""
    amount = abs(v)
    if amount >= 10_000_000:
        return f"{sign}€{amount / 1_000_000:.1f}m"
    if amount >= 950_000:
        return f"{sign}€{amount / 1_000_000:.2f}m"
    return f"{sign}€{amount / 1_000:.0f}k"


def _plot_irr_marker(
    ax: Any,
    y_value: float,
    value: float,
    *,
    color: str,
    is_portfolio: bool,
) -> None:
    ax.plot(
        float(value * 100),
        y_value,
        "o",
        color=color,
        markersize=10 if is_portfolio else 8,
        zorder=4,
        markeredgewidth=1.8 if is_portfolio else 0,
        markeredgecolor=palette["background"] if is_portfolio else "none",
    )


def _plot_missing_irr_marker(
    ax: Any,
    y_value: float,
    *,
    color: str,
    hurdle_pct: float,
) -> None:
    ax.plot(
        hurdle_pct * 0.4,
        y_value,
        "D",
        color=color,
        markersize=6,
        zorder=4,
        markerfacecolor="none",
        markeredgewidth=1.2,
    )


def _label_option_a_irr(
    ax: Any,
    y_value: float,
    value: float,
    *,
    row_fraction: float,
    label_gap: float,
    x_min: float,
    x_span: float,
    fontsize: int,
    fontweight: str,
) -> None:
    percent = float(value * 100)
    enough_left_room = (percent - x_min) >= x_span * 0.08
    if enough_left_room:
        ax.text(
            percent - label_gap,
            y_value,
            f"{percent:.0f}%",
            ha="right",
            va="center",
            fontsize=fontsize,
            fontweight=fontweight,
            color=palette["primary"],
            clip_on=True,
        )
        return

    y_offset = -0.32 if row_fraction > 0.5 else 0.32
    ax.text(
        percent,
        y_value + y_offset,
        f"{percent:.0f}%",
        ha="center",
        va="top" if y_offset < 0 else "bottom",
        fontsize=fontsize,
        fontweight=fontweight,
        color=palette["primary"],
        clip_on=True,
    )


def _label_option_b_irr(
    ax: Any,
    y_value: float,
    value: float,
    *,
    label_gap: float,
    x_max: float,
    fontsize: int,
    fontweight: str,
) -> None:
    percent = float(value * 100)
    x_position = min(percent + label_gap, x_max - label_gap)
    ax.text(
        x_position,
        y_value,
        f"{percent:.0f}%",
        ha="left",
        va="center",
        fontsize=fontsize,
        fontweight=fontweight,
        color=palette["secondary"],
        clip_on=True,
    )


def _draw_irr_row(
    ax: Any,
    i: int,
    n: int,
    y_arr: Any,
    a: float,
    b: float,
    is_portfolio: bool,
    x_min: float,
    x_max: float,
    x_span: float,
    hurdle_pct: float,
) -> None:
    lw = 2.2 if is_portfolio else 1.2
    a_ok = not math.isnan(a)
    b_ok = not math.isnan(b)
    y_value = y_arr[i]

    if a_ok and b_ok:
        ax.plot(
            [float(a * 100), float(b * 100)],
            [y_value, y_value],
            color=palette["neutral"],
            linewidth=lw,
            alpha=0.4,
            zorder=2,
        )

    if a_ok:
        _plot_irr_marker(
            ax, y_value, a, color=palette["primary"], is_portfolio=is_portfolio
        )
    else:
        _plot_missing_irr_marker(
            ax, y_value, color=palette["primary"], hurdle_pct=hurdle_pct
        )

    if b_ok:
        _plot_irr_marker(
            ax, y_value, b, color=palette["secondary"], is_portfolio=is_portfolio
        )
    else:
        _plot_missing_irr_marker(
            ax,
            y_value,
            color=palette["secondary"],
            hurdle_pct=hurdle_pct,
        )

    label_gap = x_span * 0.012
    fs = 9 if is_portfolio else 8
    fw = "bold" if is_portfolio else "normal"

    if a_ok:
        row_fraction = y_value / max(n - 1, 1)
        _label_option_a_irr(
            ax,
            y_value,
            a,
            row_fraction=row_fraction,
            label_gap=label_gap,
            x_min=x_min,
            x_span=x_span,
            fontsize=fs,
            fontweight=fw,
        )

    if b_ok:
        _label_option_b_irr(
            ax,
            y_value,
            b,
            label_gap=label_gap,
            x_max=x_max,
            fontsize=fs,
            fontweight=fw,
        )


def plot_irr_feature_chart(
    rows: list[tuple],
    portfolio_irr_a: float,
    portfolio_irr_b: float,
    hurdle_rate: float = 0.08,
    *,
    title: str = "IRR per Feature — Option A vs. Option B",
) -> None:
    """Horizontal lollipop chart comparing IRR_A and IRR_B for each feature.

    Each feature is a row. Two dots (Option A blue, Option B green) are
    connected by a thin line — the gap shows the IRR lift from spreading
    installments. A vertical dashed hurdle-rate line divides the chart into
    a below-threshold zone (light red) and an above-threshold zone (light
    green). The portfolio aggregate appears at the top as a bolder row.

    Parameters
    ----------
    rows:
        Output of ``BlockchainCaseStudyService.irr_dual_rows()``.
        Each row: ``(name, dev_cost, installment, inst_years,
        a_exp, a_floor, a_ceil, b_exp, b_floor, b_ceil)``.
    portfolio_irr_a:
        Portfolio-level IRR under upfront financing.
    portfolio_irr_b:
        Portfolio-level IRR under installment financing.
    hurdle_rate:
        Minimum required return — shown as a vertical reference line.
    title:
        Chart title.
    """
    # ── Data preparation ───────────────────────────────────────────────────
    names = [r[0] for r in rows]
    a_vals = [r[4] for r in rows]  # a_exp
    b_vals = [r[7] for r in rows]  # b_exp

    # Sort features by IRR_B descending (NaN → bottom)
    order = sorted(
        range(len(names)),
        key=lambda i: (
            not math.isnan(b_vals[i]),
            b_vals[i] if not math.isnan(b_vals[i]) else -1,
        ),
        reverse=True,
    )
    names = [names[i] for i in order]
    a_vals = [a_vals[i] for i in order]
    b_vals = [b_vals[i] for i in order]

    # Portfolio row inserted at the top
    all_names = ["Portfolio", *names]
    all_a = [portfolio_irr_a, *a_vals]
    all_b = [portfolio_irr_b, *b_vals]

    n = len(all_names)
    y = np.arange(n)

    # X-axis range: accommodate negative IRRs on the left, cap at 300 % on right
    finite_vals = [v * 100 for v in all_a + all_b if not math.isnan(v)]
    x_min = min(0.0, min(finite_vals) * 1.15) if finite_vals else 0.0
    x_max = min(max(finite_vals) * 1.25, 300) if finite_vals else 100
    x_max = max(x_max, hurdle_rate * 100 * 1.5)
    hurdle_pct = hurdle_rate * 100
    x_span = x_max - x_min

    # ── Figure ──────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 0.75 * n + 1.8))

    # Background zones — below/above hurdle
    ax.axvspan(x_min, hurdle_pct, alpha=0.06, color=palette["danger"], zorder=0)
    ax.axvspan(hurdle_pct, x_max, alpha=0.04, color=palette["success"], zorder=0)

    # Hurdle line — label inside top of the chart (y = n-1, the topmost row)
    ax.axvline(
        hurdle_pct, color=palette["warning"], linewidth=1.5, linestyle="--", zorder=1
    )
    ax.text(
        hurdle_pct + x_span * 0.01,
        n - 1,
        f"hurdle {hurdle_rate:.0%}",
        color=palette["warning"],
        fontsize=8,
        va="center",
        ha="left",
    )

    # ── Draw each row ────────────────────────────────────────────────────
    for i, (_name, a, b) in enumerate(zip(all_names, all_a, all_b, strict=False)):
        _draw_irr_row(ax, i, n, y, a, b, i == 0, x_min, x_max, x_span, hurdle_pct)

    # Separator line after portfolio row
    ax.axhline(n - 1.5, color=palette["border"], linewidth=1.2, linestyle="-", zorder=1)

    # Y-axis labels — bold for portfolio
    ax.set_yticks(y)
    ax.set_yticklabels(
        [f"$\\bf{{{n}}}$" if i == 0 else n for i, n in enumerate(all_names)],
        fontsize=10,
    )

    ax.set_xlim(x_min, x_max)
    ax.set_xlabel("Internal Rate of Return (%)", fontsize=11)
    ax.set_title(
        _title_without_hurdle_note(title), fontsize=13, fontweight="bold", pad=14
    )
    ax.xaxis.set_major_formatter(plt.FuncFormatter(_pct_formatter))

    # Legend
    legend_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=palette["primary"],
            markersize=9,
            label=OPTION_A_UPFRONT_LABEL,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=palette["secondary"],
            markersize=9,
            label=OPTION_B_INSTALLMENT_LABEL,
        ),
    ]
    ax.legend(
        handles=legend_handles,
        loc="lower right",
        fontsize=9,
        framealpha=0.88,
        edgecolor=palette["border"],
    )

    _apply_axis_style(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(left=False)
    plt.tight_layout()
    _show_fig(fig)


def _annotate_irr_a(
    ax: Any,
    irr_a: float | None,
    irr_a_in_range: bool,
    close_irr_labels: bool,
    x_max: float,
    x_rate_max: float,
) -> None:
    if irr_a_in_range and irr_a is not None:
        ax.plot(irr_a * 100, 0, "o", color=palette["primary"], markersize=8, zorder=5)
        if close_irr_labels:
            offset_x = -18
        elif irr_a * 100 > x_max * 0.85:
            offset_x = -10
        else:
            offset_x = 10
        ax.annotate(
            f"IRR_A = {irr_a:.0%}",
            xy=(irr_a * 100, 0),
            xytext=(offset_x, 14),
            textcoords=ANNOTATION_TEXTCOORDS,
            color=palette["primary"],
            fontsize=8.5,
            fontweight="bold",
            ha="right" if offset_x < 0 else "left",
            va="bottom",
            bbox={
                "boxstyle": "round,pad=0.3",
                "facecolor": palette["background"],
                "edgecolor": palette["primary"],
                "linewidth": 0.8,
                "alpha": 0.92,
            },
            annotation_clip=False,
        )
    elif irr_a is not None and not irr_a_in_range:
        irr_a_note = f"IRR_A > {x_max:.0f}%" if irr_a > x_rate_max else "IRR_A < 0%"
        ax.text(
            0.02,
            0.18,
            irr_a_note,
            transform=ax.transAxes,
            color=palette["primary"],
            fontsize=8,
            style="italic",
            va="bottom",
            ha="left",
            bbox={
                "boxstyle": CALLOUT_BOXSTYLE,
                "facecolor": palette["background"],
                "edgecolor": palette["primary"],
                "linewidth": 0.8,
                "alpha": 0.92,
            },
        )
    else:
        ax.text(
            0.02,
            0.18,
            "IRR_A: no finite crossing",
            transform=ax.transAxes,
            color=palette["primary"],
            fontsize=8,
            style="italic",
            va="bottom",
            ha="left",
            bbox={
                "boxstyle": CALLOUT_BOXSTYLE,
                "facecolor": palette["background"],
                "edgecolor": palette["primary"],
                "linewidth": 0.8,
                "alpha": 0.92,
            },
        )


def _annotate_irr_b(
    ax: Any,
    irr_b: float | None,
    irr_b_in_range: bool,
    close_irr_labels: bool,
    x_max: float,
    x_rate_max: float,
) -> None:
    if irr_b_in_range and irr_b is not None:
        ax.plot(irr_b * 100, 0, "o", color=palette["secondary"], markersize=8, zorder=5)
        if close_irr_labels:
            offset_x = 18
        elif irr_b * 100 > x_max * 0.85:
            offset_x = -10
        else:
            offset_x = 10
        ax.annotate(
            f"IRR_B = {irr_b:.0%}",
            xy=(irr_b * 100, 0),
            xytext=(offset_x, -16),
            textcoords=ANNOTATION_TEXTCOORDS,
            color=palette["secondary"],
            fontsize=8.5,
            fontweight="bold",
            ha="right" if offset_x < 0 else "left",
            va="top",
            bbox={
                "boxstyle": "round,pad=0.3",
                "facecolor": palette["background"],
                "edgecolor": palette["secondary"],
                "linewidth": 0.8,
                "alpha": 0.92,
            },
            annotation_clip=False,
        )
    elif irr_b is None:
        ax.text(
            0.02,
            0.12,
            "IRR_B: no finite crossing",
            transform=ax.transAxes,
            color=palette["secondary"],
            fontsize=8,
            style="italic",
            va="bottom",
            ha="left",
            bbox={
                "boxstyle": CALLOUT_BOXSTYLE,
                "facecolor": palette["background"],
                "edgecolor": palette["secondary"],
                "linewidth": 0.8,
                "alpha": 0.92,
            },
        )
    else:
        irr_b_note = f"IRR_B > {x_max:.0f}%" if irr_b > x_rate_max else "IRR_B < 0%"
        ax.text(
            0.02,
            0.12,
            irr_b_note,
            transform=ax.transAxes,
            color=palette["secondary"],
            fontsize=8,
            style="italic",
            va="bottom",
            ha="left",
            bbox={
                "boxstyle": CALLOUT_BOXSTYLE,
                "facecolor": palette["background"],
                "edgecolor": palette["secondary"],
                "linewidth": 0.8,
                "alpha": 0.92,
            },
        )


def _resolve_irr_pair(
    cashflows_a: list[float],
    cashflows_b: list[float],
    irr_a: float | None,
    irr_b: float | None,
) -> tuple[float | None, float | None]:
    return (
        _find_non_negative_irr(cashflows_a) if irr_a is None else irr_a,
        _find_non_negative_irr(cashflows_b) if irr_b is None else irr_b,
    )


def _hurdle_label_offsets(
    hurdle_x: float,
    x_max: float,
    hurdle_npv_a: float,
    hurdle_npv_b: float,
) -> tuple[tuple[int, int], tuple[int, int]]:
    first, second = (-16, -28), (16, 24)
    if hurdle_npv_a > hurdle_npv_b:
        first, second = (-16, 24), (16, -28)

    if hurdle_x < x_max * 0.18:
        first, second = (18, -30), (18, 26)
        if hurdle_npv_a > hurdle_npv_b:
            first, second = (18, 26), (18, -30)
    elif hurdle_x > x_max * 0.82:
        first, second = (-18, -30), (-18, 26)
        if hurdle_npv_a > hurdle_npv_b:
            first, second = (-18, 26), (-18, -30)

    return first, second


def _title_without_hurdle_note(title: str) -> str:
    marker = " (hurdle "
    if marker not in title:
        return title
    return title[: title.index(marker)]


def _capitalized_rate_label(rate: float) -> str:
    return f"Hurdle {rate:.0%}"


def plot_npv_rate_curve(
    cashflows_a: list[float],
    cashflows_b: list[float],
    hurdle_rate: float = 0.08,
    irr_a: float | None = None,
    irr_b: float | None = None,
    *,
    title: str = "NPV vs. Discount Rate — Option A vs. Option B",
) -> None:
    """NPV as a function of discount rate for Option A and Option B.

    - **Option A** (blue): large Year-0 outlay, NPV crosses zero at IRR_A.
    - **Option B** (green): smaller Year-0 installment, NPV crosses zero at a
      higher IRR_B because less capital is at risk in Year 0.

    Parameters
    ----------
    cashflows_a:
        Portfolio net cashflows under Option A: ``[-investment, +net_yr1, ...]``.
    cashflows_b:
        Portfolio net cashflows under Option B: ``[-first_inst, +net_yr1, ...]``.
    hurdle_rate:
        The organisation's minimum required return — shown as a vertical line.
    irr_a:
        Pre-computed IRR for Option A (optional). Derived from cashflows if None.
    irr_b:
        Pre-computed IRR for Option B (optional). Annotated when within display range.
    title:
        Chart title.
    """
    display_rate_cap = 8.0  # 800% max to keep charts readable in notebooks.
    irr_a, irr_b = _resolve_irr_pair(cashflows_a, cashflows_b, irr_a, irr_b)

    x_rate_max = min(max(0.40, hurdle_rate * 5.0), display_rate_cap)
    rates = np.linspace(0.0, x_rate_max, 500)

    npv_a = np.array([_npv_value(cashflows_a, r) for r in rates])
    npv_b = np.array([_npv_value(cashflows_b, r) for r in rates])

    x_max = rates[-1] * 100
    hurdle_x = hurdle_rate * 100

    fig, ax = plt.subplots(figsize=(14.8, 6.2))

    x_values = rates * 100
    b_beats_a = npv_b >= npv_a
    ax.fill_between(
        x_values,
        npv_a,
        npv_b,
        where=b_beats_a,
        interpolate=True,
        color=palette["secondary"],
        alpha=0.08,
        zorder=1,
    )
    ax.fill_between(
        x_values,
        npv_a,
        npv_b,
        where=~b_beats_a,
        interpolate=True,
        color=palette["danger"],
        alpha=0.06,
        zorder=1,
    )

    ax.plot(x_values, npv_a, color=palette["primary"], linewidth=2.8, zorder=3)
    ax.plot(x_values, npv_b, color=palette["secondary"], linewidth=2.8, zorder=3)

    ax.axvspan(0, hurdle_x, color=palette["surface"], alpha=0.82, zorder=0)
    ax.axhline(0, color=palette["neutral"], linewidth=1.1, alpha=0.72, zorder=0)

    ax.axvline(
        hurdle_x,
        color=palette["warning"],
        linewidth=2.4,
        linestyle=(0, (6, 3)),
        alpha=0.96,
        zorder=4,
    )

    # ── Y-axis scale and annotation padding ────────────────────────────────
    y_top = max(float(npv_a.max()), float(npv_b.max()))
    y_bot = min(float(npv_a.min()), float(npv_b.min()))
    y_span = max(y_top - y_bot, 1.0)
    y_padding = y_span * 0.18
    ax.set_ylim(y_bot - y_padding, y_top + y_padding)

    label_gap = y_span * 0.035
    end_label_x = x_max + 1.2
    ax.text(
        end_label_x,
        npv_a[-1] - label_gap,
        "Option A",
        color=palette["primary"],
        fontsize=10,
        fontweight="bold",
        va="center",
        ha="left",
        clip_on=False,
    )
    ax.text(
        end_label_x,
        npv_b[-1] + label_gap,
        "Option B",
        color=palette["secondary"],
        fontsize=10,
        fontweight="bold",
        va="center",
        ha="left",
        clip_on=False,
    )

    ax.text(
        hurdle_x,
        -0.12,
        _capitalized_rate_label(hurdle_rate),
        transform=ax.get_xaxis_transform(),
        color=palette["warning"],
        fontsize=9,
        fontweight="bold",
        va="top",
        ha="center",
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": palette["background"],
            "edgecolor": palette["warning"],
            "linewidth": 0.8,
            "alpha": 0.94,
        },
        clip_on=False,
        zorder=8,
    )

    hurdle_npv_a = _npv_value(cashflows_a, hurdle_rate)
    hurdle_npv_b = _npv_value(cashflows_b, hurdle_rate)
    for value, color in (
        (hurdle_npv_a, palette["primary"]),
        (hurdle_npv_b, palette["secondary"]),
    ):
        ax.scatter(
            [hurdle_x],
            [value],
            s=72,
            facecolor=palette["background"],
            edgecolor=color,
            linewidth=2.0,
            zorder=6,
        )

    lift = hurdle_npv_b - hurdle_npv_a
    lift_sign = "+" if lift >= 0 else ""
    lift_color = palette["secondary"] if lift >= 0 else palette["danger"]
    ax.annotate(
        f"B - A {lift_sign}{_eur_compact(lift)} at hurdle",
        xy=(hurdle_x, max(hurdle_npv_a, hurdle_npv_b)),
        xytext=(14 if hurdle_x < x_max * 0.72 else -14, 18),
        textcoords=ANNOTATION_TEXTCOORDS,
        ha="left" if hurdle_x < x_max * 0.72 else "right",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        color=lift_color,
        bbox={
            "boxstyle": "round,pad=0.36",
            "facecolor": palette["background"],
            "edgecolor": lift_color,
            "linewidth": 1.0,
            "alpha": 0.96,
        },
        arrowprops={"arrowstyle": "-", "color": lift_color, "linewidth": 1.0},
        zorder=7,
        annotation_clip=False,
    )

    irr_a_text = "not finite" if irr_a is None else f"{irr_a:.0%}"
    irr_b_text = "not finite" if irr_b is None else f"{irr_b:.0%}"
    summary_text = (
        "Decision lens | "
        f"NPV @ {hurdle_rate:.0%}: A {_eur_compact(hurdle_npv_a)}  "
        f"B {_eur_compact(hurdle_npv_b)}  |  "
        f"Gap: {lift_sign}{_eur_compact(lift)}\n"
        f"IRR: A {irr_a_text}  B {irr_b_text}"
    )
    fig.text(
        0.5,
        0.035,
        summary_text,
        ha="center",
        va="bottom",
        fontsize=9.5,
        fontweight="bold",
        color=palette["neutral"],
        bbox={
            "boxstyle": "round,pad=0.42",
            "facecolor": palette["surface"],
            "edgecolor": palette["border"],
            "linewidth": 1.0,
            "alpha": 0.97,
        },
        zorder=7,
    )

    # ── IRR crossing labels — inline, no arrows ────────────────────────────
    # Display range is 0%..x_max (x-axis), so negative IRRs are out of range.
    irr_a_in_range = irr_a is not None and 0.0 <= irr_a <= x_rate_max
    irr_b_in_range = irr_b is not None and 0.0 <= irr_b <= x_rate_max
    close_irr_labels = (
        irr_a_in_range
        and irr_b_in_range
        and irr_a is not None
        and irr_b is not None
        and abs((irr_a - irr_b) * 100) < 8.0
    )

    if irr_a_in_range:
        _annotate_irr_a(ax, irr_a, irr_a_in_range, close_irr_labels, x_max, x_rate_max)
    if irr_b_in_range:
        _annotate_irr_b(ax, irr_b, irr_b_in_range, close_irr_labels, x_max, x_rate_max)

    ax.set_title(title, fontsize=13, fontweight="bold", pad=14)
    ax.set_xlabel("Discount Rate (%)", fontsize=11)
    ax.set_ylabel("Net Present Value (€)", fontsize=11, fontweight="bold")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"€{v / 1_000:.0f}k"))
    ax.tick_params(axis="y", labelsize=10)
    ax.set_xlim(0, x_max + 3)

    _apply_axis_style(ax)
    ax.grid(axis="x", alpha=0.06, linewidth=0.7)
    plt.tight_layout(rect=(0, 0.18, 1, 1))
    _show_fig(fig)


def plot_cashflow_bars(
    sched_a: dict,
    sched_b: dict,
    *,
    title: str = "Net Cash Flow per Year — Option A vs. Option B",
) -> None:
    """Grouped bar chart showing portfolio net cashflows year by year.

    Each year has two bars side by side:

    - **Blue** (Option A): large negative bar at Year 0, positive in Years 1-3.
    - **Green** (Option B): no Year 0 bar, positive in Years 1-3 (lower than A
      during installment years, equal after).

    This makes the core financing difference immediately visible to a C-level
    audience without reading a table.

    Parameters
    ----------
    sched_a:
        Option A schedule from ``BlockchainCaseStudyService.feature_cashflow_schedules()``.
        Uses the ``portfolio`` sub-dict which has ``cashflows`` and ``npv``.
    sched_b:
        Option B schedule (same structure).
    title:
        Chart title.
    """
    port_a = sched_a["portfolio"]["cashflows"]
    port_b = sched_b["portfolio"]["cashflows"]
    years = sched_a["years"]
    year_labels = [f"Year {y}" for y in years]

    x = np.arange(len(years))
    width = 0.38

    fig, ax = plt.subplots(figsize=FIG.wide)

    bars_a = ax.bar(
        x - width / 2,
        port_a,
        width,
        label=OPTION_A_UPFRONT_LABEL,
        color=[palette["danger"] if v < 0 else palette["primary"] for v in port_a],
        edgecolor=palette["background"],
        linewidth=0.6,
    )
    bars_b = ax.bar(
        x + width / 2,
        port_b,
        width,
        label=OPTION_B_INSTALLMENT_LABEL,
        color=palette["secondary"],
        edgecolor=palette["background"],
        linewidth=0.6,
    )

    # Value labels on bars
    for bar in [*bars_a, *bars_b]:
        h = bar.get_height()
        if abs(h) < 1:
            continue
        sign = "+" if h >= 0 else "−"
        va = "bottom" if h >= 0 else "top"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h + (3_000 if h >= 0 else -3_000),
            f"{sign}€{abs(h):,.0f}",
            ha="center",
            va=va,
            fontsize=8,
            color=palette["neutral"],
        )

    ax.axhline(0, color=palette["border"], linewidth=0.8, zorder=0)
    ax.set_xticks(x)
    ax.set_xticklabels(year_labels, fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=14)
    ax.set_ylabel("Net Cash Flow (€)", fontsize=11)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"€{v / 1_000:+.0f}k"))

    _apply_axis_style(ax)

    legend_handles = [
        Patch(facecolor=palette["primary"], label="Option A — positive year"),
        Patch(facecolor=palette["danger"], label="Option A — investment outflow"),
        Patch(facecolor=palette["secondary"], label=OPTION_B_INSTALLMENT_LABEL),
    ]
    ax.legend(handles=legend_handles, loc="lower right", fontsize=9, framealpha=0.85)

    npv_a = sched_a["portfolio"]["npv"]
    npv_b = sched_b["portfolio"]["npv"]
    benefit = npv_b - npv_a
    sign = "+" if benefit >= 0 else "−"
    ax.annotate(
        f"NPV A = €{npv_a:,.0f}  |  NPV B = €{npv_b:,.0f}  |  Benefit {sign}€{abs(benefit):,.0f}",
        xy=(0.5, -0.13),
        xycoords=AXES_FRACTION,
        ha="center",
        fontsize=9,
        color=palette["neutral"],
        style="italic",
    )

    plt.tight_layout()
    _show_fig(fig)


def plot_npv_comparison(
    npv_a_expected: float,
    npv_a_floor: float,
    npv_a_ceiling: float,
    npv_b_expected: float,
    npv_b_floor: float,
    npv_b_ceiling: float,
    pi_a: float,
    pi_b: float,
    discount_rate: float = 0.0,
    *,
    title: str = "Portfolio NPV — Option A vs. Option B",
) -> None:
    """Executive NPV comparison with a calm two-option layout.

    The chart keeps the decision signal separate from the data marks:
    expected NPV is shown as the main bar, the Option B lift is a top badge,
    and risk/efficiency details sit in compact labels away from the bars.

    Parameters
    ----------
    npv_a_expected, npv_a_floor, npv_a_ceiling:
        Expected, VaR 95% (5th pctl), and P95 (95th pctl) for Option A.
    npv_b_expected, npv_b_floor, npv_b_ceiling:
        Same for Option B.
    pi_a, pi_b:
        Profitability Index for each option.
    discount_rate:
        Shown in the panel footer.
    title:
        Chart title.
    """
    labels = ["Option A\nUpfront", "Option B\nInstallment"]
    expected = [npv_a_expected, npv_b_expected]
    floors = [npv_a_floor, npv_b_floor]
    ceilings = [npv_a_ceiling, npv_b_ceiling]
    colors = [palette["primary"], palette["secondary"]]
    pis = [pi_a, pi_b]

    y_max = max(npv_a_expected, npv_b_expected, npv_a_ceiling, npv_b_ceiling)
    y_min = min(npv_a_expected, npv_b_expected, npv_a_floor, npv_b_floor, 0.0)
    y_span = max(y_max - y_min, 1.0)
    label_gap = y_span * 0.055

    fig, ax = plt.subplots(figsize=(9.8, 6.2))

    bars = ax.bar(
        labels,
        expected,
        color=colors,
        width=0.46,
        alpha=0.92,
        edgecolor=palette["background"],
        linewidth=1.4,
        zorder=3,
    )

    # Keep the full bar geometry visible even when all expected NPVs are negative.
    # Matplotlib bars start at 0, so the upper range must include the baseline.
    y_lower = min(0.0, y_min, *expected, *floors) - y_span * 0.18
    y_upper = max(0.0, y_max, *expected, *ceilings) + y_span * 0.32
    ax.set_ylim(y_lower, y_upper)

    for bar, exp, color, pi in zip(bars, expected, colors, pis, strict=False):
        cx = bar.get_x() + bar.get_width() / 2
        badge_text_color = palette["background"]

        # PI centered using actual bar geometry (works for positive/negative bars).
        cy = bar.get_y() + bar.get_height() / 2
        ax.text(
            cx,
            cy,
            f"PI  {pi:.2f}\u00d7",
            ha="center",
            va="center",
            fontsize=12,
            fontweight="bold",
            color=badge_text_color,
            zorder=4,
            bbox={
                "boxstyle": "round,pad=0.22",
                "facecolor": color,
                "edgecolor": badge_text_color,
                "linewidth": 0.8,
                "alpha": 0.98,
            },
        )

        value_y = exp + label_gap if exp >= 0 else exp - label_gap
        value_va = "bottom" if exp >= 0 else "top"
        ax.text(
            cx,
            value_y,
            f"Expected\n{_eur_readable(exp)}",
            ha="center",
            va=value_va,
            fontsize=11,
            fontweight="bold",
            color=palette["neutral"],
            zorder=4,
            bbox={
                "boxstyle": "round,pad=0.38",
                "facecolor": palette["background"],
                "edgecolor": color,
                "linewidth": 0.9,
                "alpha": 0.96,
            },
        )

    for bar, floor, ceiling, color in zip(bars, floors, ceilings, colors, strict=False):
        cx = bar.get_x() + bar.get_width() / 2
        rail_x = cx + 0.34
        ax.vlines(
            rail_x,
            floor,
            ceiling,
            color=color,
            linewidth=2.4,
            alpha=0.56,
            zorder=2,
        )
        ax.scatter(
            [rail_x, rail_x],
            [floor, ceiling],
            s=36,
            color=palette["background"],
            edgecolor=color,
            linewidth=1.5,
            zorder=5,
        )

        detail_y = y_lower + (y_upper - y_lower) * 0.055
        ax.text(
            cx,
            detail_y,
            f"P95 {_eur_compact(ceiling)}  |  BVF {_eur_compact(floor)}",
            ha="center",
            va="bottom",
            fontsize=8.8,
            fontweight="bold",
            color=color,
            zorder=5,
        )

    ax.axhline(0, color=palette["border"], linewidth=1.0, zorder=1)

    benefit = npv_b_expected - npv_a_expected
    sign = "+" if benefit >= 0 else "\u2212"
    bc = palette["secondary"] if benefit >= 0 else palette["danger"]
    display_title = _title_without_hurdle_note(title)
    fig.suptitle(display_title, fontsize=13, fontweight="bold", y=0.985)
    fig.text(
        0.5,
        0.925,
        f"Option B lift: {sign}{_eur_readable(abs(benefit))}",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color=bc,
        bbox={
            "boxstyle": "round,pad=0.42",
            "facecolor": palette["background"],
            "edgecolor": bc,
            "linewidth": 1.0,
            "alpha": 0.97,
        },
    )

    ax.set_ylabel("Net Present Value (\u20ac)", fontsize=11)
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda v, _: f"\u20ac{v / 1_000:.0f}k")
    )
    ax.tick_params(labelsize=11)
    ax.text(
        0.5,
        -0.14,
        f"Thin side rails show BVF-to-P95 risk range. {_capitalized_rate_label(discount_rate)}.",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=9,
        color=palette["subtle"],
    )
    _apply_axis_style(ax)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.margins(x=0.28)
    plt.tight_layout(rect=(0, 0.08, 1, 0.88))
    _show_fig(fig)
