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

"""Shared helpers for chart modules."""

from __future__ import annotations

import importlib
import math

import matplotlib.pyplot as plt

from ..styling import palette

_DEFAULT_COLORS = [
    palette["primary"],  # blue
    palette["secondary"],  # green
    palette["accent"],  # purple
    palette["danger"],  # red
    palette["tertiary"],  # teal
]


def _show_fig(fig: object) -> None:
    """Display a matplotlib figure exactly once and close it to free memory.

    Uses ``IPython.display.display()`` when running inside Jupyter so the
    figure is rendered by the display machinery rather than by ``plt.show()``.
    This prevents double-rendering under ``%matplotlib inline``, where both
    an explicit ``plt.show()`` call and the post-execute ``flush_figures()``
    hook would otherwise display the same figure.

    Falls back to ``plt.show()`` in script / test contexts (no IPython kernel).
    """
    try:
        ipython_mod = importlib.import_module("IPython")
    except ImportError:
        plt.show()
        plt.close(fig)  # type: ignore[arg-type]
        return

    get_ipython_fn = getattr(ipython_mod, "get_ipython", None)
    if callable(get_ipython_fn) and get_ipython_fn() is not None:
        try:
            display_mod = importlib.import_module("IPython.display")
            display_fn = getattr(display_mod, "display", None)
            if callable(display_fn):
                display_fn(fig)
                plt.close(fig)  # type: ignore[arg-type]
                return
        except ImportError:
            pass

    plt.show()
    plt.close(fig)  # type: ignore[arg-type]


def _cycle_colors(n: int, colors: list[str] | None = None) -> list[str]:
    """Return *n* colours, cycling through *colors* if fewer are given."""
    c = colors or _DEFAULT_COLORS
    return [c[i % len(c)] for i in range(n)]


def _label_line(ax, x: float, y: float, text: str, color: str) -> None:
    """Place a readable label for a vertical reference line.

    If ``y`` is > 0, the label is placed in data coordinates at ``(x, y)``.
    Otherwise, it is placed above the x-axis using axis transform.
    """
    use_data_coords = y > 0
    if use_data_coords:
        y_low, y_high = ax.get_ylim()
        span = max(y_high - y_low, 1e-9)
        y_pos = min(max(y, y_low + span * 0.06), y_high - span * 0.06)
        transform = ax.transData
        va = "center"
        rotation = 0
    else:
        y_pos = 1.01
        transform = ax.get_xaxis_transform()
        va = "bottom"
        rotation = 18

    ax.text(
        x,
        y_pos,
        text,
        transform=transform,
        ha="center",
        va=va,
        rotation=rotation,
        fontsize=9,
        color=color,
        fontweight="bold",
        clip_on=False,
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": palette["background"],
            "edgecolor": color,
            "alpha": 0.95,
        },
    )


def _annotate_vertical_callouts(
    ax,
    markers: list[tuple[float, str, str]],
    *,
    y_fracs: tuple[float, ...] = (1.24, 1.16, 1.24),
    min_gap_frac: float = 0.08,
    x_pad: tuple[float, float] = (0.06, 0.94),
    fontsize: float = 8.5,
    text_va: str = "top",
) -> None:
    """Annotate vertical markers with offset callouts above the chart.

    The helper separates labels horizontally when quantiles are close so labels
    remain readable instead of sitting directly on the reference lines.
    """
    if not markers:
        return

    x_min, x_max = ax.get_xlim()
    x_span = max(x_max - x_min, 1e-9)
    left, right = x_pad

    sorted_markers = sorted(markers, key=lambda item: item[0])
    proposed = [float((x - x_min) / x_span) for x, _, _ in sorted_markers]
    adjusted: list[float] = []
    for p in proposed:
        p_clamped = max(left, min(right, p))
        if not adjusted:
            adjusted.append(p_clamped)
            continue
        adjusted.append(max(p_clamped, adjusted[-1] + min_gap_frac))

    overflow = adjusted[-1] - right
    if overflow > 0:
        adjusted = [max(left, v - overflow) for v in adjusted]

    for idx, ((x_val, text, color), x_frac) in enumerate(
        zip(sorted_markers, adjusted, strict=False)
    ):
        y_frac = y_fracs[idx % len(y_fracs)]
        ax.annotate(
            text,
            xy=(x_val, 0.97),
            xycoords=ax.get_xaxis_transform(),
            xytext=(x_frac, y_frac),
            textcoords=ax.transAxes,
            ha="center",
            va=text_va,
            fontsize=fontsize,
            color=color,
            fontweight="bold",
            annotation_clip=False,
            arrowprops={
                "arrowstyle": "-|>",
                "color": color,
                "lw": 1.0,
                "shrinkA": 3,
                "shrinkB": 1,
            },
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": palette["surface"],
                "edgecolor": color,
                "alpha": 0.96,
            },
        )


def _place_bottom_legend(
    fig,
    handles: list,
    labels: list[str],
    *,
    max_cols: int = 4,
    title: str | None = None,
    fontsize: float = 9.0,
) -> float:
    """Place a figure legend below the plot and return recommended bottom padding.

    This keeps legends readable and avoids overlap with axes, tick labels, and titles.
    """
    clean = [
        (h, lbl)
        for h, lbl in zip(handles, labels, strict=False)
        if lbl and not str(lbl).startswith("_")
    ]
    if not clean:
        return 0.0

    legend_handles = [item[0] for item in clean]
    legend_labels = [item[1] for item in clean]
    n_items = len(legend_labels)
    ncol = min(max_cols, n_items)
    rows = math.ceil(n_items / ncol)

    legend = fig.legend(
        legend_handles,
        legend_labels,
        loc="lower center",
        ncol=ncol,
        fontsize=fontsize,
        frameon=True,
        fancybox=True,
        shadow=False,
        framealpha=0.95,
        handlelength=2.0,
        columnspacing=1.2,
        borderpad=0.6,
        title=title,
        title_fontsize=max(fontsize, 9.5) if title else None,
        # Keep legend inside figure bounds to avoid clipping in notebooks,
        # while staying low enough to not compete with axis labels.
        bbox_to_anchor=(0.5, 0.005),
    )

    # Draw once to measure the rendered legend in figure coordinates.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    legend_bbox = legend.get_window_extent(renderer=renderer).transformed(
        fig.transFigure.inverted()
    )
    legend_height = max(float(legend_bbox.height), 0.0)
    legend_top = max(float(legend_bbox.y1), 0.0)

    # Reserve bottom space for x tick labels + x-axis title + legend.
    # Use measured legend top for robust spacing across figure sizes and DPI.
    return min(
        0.40,
        max(
            0.14,
            legend_top
            + 0.06
            + (rows - 1) * 0.01
            + (0.01 if title else 0.0)
            + max(0.0, legend_height - 0.06) * 0.25,
        ),
    )


def _apply_axis_style(ax, *, grid_axis: str = "y") -> None:
    """Apply consistent enterprise-like axis styling."""
    ax.grid(axis=grid_axis, alpha=0.18, linewidth=0.8)
    ax.spines[["left", "bottom"]].set_color(palette["border"])
    ax.spines[["left", "bottom"]].set_linewidth(0.9)
    ax.tick_params(axis="both", labelsize=10, pad=4)

    # Global readability baseline for axis descriptions across all chart modules.
    if ax.get_xlabel():
        ax.xaxis.label.set_fontsize(max(ax.xaxis.label.get_size(), 10))
        ax.xaxis.labelpad = max(float(ax.xaxis.labelpad), 8.0)
    if ax.get_ylabel():
        ax.yaxis.label.set_fontsize(max(ax.yaxis.label.get_size(), 10))
        ax.yaxis.labelpad = max(float(ax.yaxis.labelpad), 8.0)


def _set_xtick_labels(
    ax,
    ticks: list | tuple,
    labels: list[str],
    *,
    rotation: float = 24.0,
    fontsize: float = 10.0,
) -> None:
    """Set readable x tick labels with safe rotation to avoid clipping."""
    ha = "right" if rotation else "center"
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, rotation=rotation, ha=ha, fontsize=fontsize)


def _hex_to_rgb01(hex_color: str) -> tuple[float, float, float]:
    """Convert a ``RRGGBB`` hex color string to 0..1 RGB."""
    raw = hex_color.strip().lstrip("#")
    if len(raw) != 6:
        return 0.0, 0.0, 0.0
    r = int(raw[0:2], 16) / 255.0
    g = int(raw[2:4], 16) / 255.0
    b = int(raw[4:6], 16) / 255.0
    return r, g, b


def _relative_luminance(hex_color: str) -> float:
    """Return relative luminance for contrast checks."""

    def _linearize(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = _hex_to_rgb01(hex_color)
    r_lin, g_lin, b_lin = _linearize(r), _linearize(g), _linearize(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def _contrast_ratio(c1: str, c2: str) -> float:
    """Return WCAG contrast ratio between two hex colors."""
    l1 = _relative_luminance(c1)
    l2 = _relative_luminance(c2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _best_text_color(
    bg_color: str,
    *,
    light: str = palette["background"],
    dark: str = palette["neutral"],
) -> str:
    """Pick readable light/dark text color for a given background color."""
    light_ratio = _contrast_ratio(bg_color, light)
    dark_ratio = _contrast_ratio(bg_color, dark)
    return light if light_ratio >= dark_ratio else dark
