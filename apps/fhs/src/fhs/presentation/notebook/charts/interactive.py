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

"""Interactive Plotly chart functions for Jupyter notebooks.

These functions mirror their Matplotlib counterparts but return Plotly figures
with hover, zoom, and export capabilities.  Use them by passing
``interactive=True`` to the chart wrappers or by calling them directly.

Available functions:
- ``plot_risk_profile_interactive``          – histogram + KPI panel
- ``plot_feature_distributions_interactive`` – overlapping outcome distributions
- ``plot_multi_year_fan_interactive``        – fan chart with confidence bands
"""

from __future__ import annotations

from typing import Any

from ..styling import palette

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    _HAS_PLOTLY = True
except ImportError:  # pragma: no cover
    go = None  # type: ignore[assignment]
    make_subplots = None  # type: ignore[assignment]
    _HAS_PLOTLY = False

# ── Palette shortcuts (no hardcoded hex) ─────────────────────────────────────
_BG = palette["background"]  # paper background
_SURFACE = palette["surface"]  # plot area background
_NEUTRAL = palette["neutral"]  # axis labels, table headers
BUSINESS_VALUE_EURO_AXIS = "Business Value (€)"
EXPECTED_BUSINESS_VALUE_LABEL = "Expected Business Value"
LINES_AND_MARKERS_MODE = "lines+markers"


def _require_plotly() -> None:
    if not _HAS_PLOTLY:  # pragma: no cover
        raise ImportError(
            "plotly is required for interactive charts. "
            "Install it with: pip install plotly"
        )


def _extra_colors() -> list[str]:
    """Return extended palette cycle for multi-feature charts."""
    return [
        palette["primary"],
        palette["secondary"],
        palette["accent"],
        palette["tertiary"],
        palette["warning"],
        palette["danger"],
    ]


def _feature_panel_color(
    idx: int,
    colors: list[str] | None,
    palette_cycle: list[str],
) -> str:
    if colors and idx < len(colors):
        return colors[idx]
    return palette_cycle[idx % len(palette_cycle)]


# ── Risk-Profile Dashboard ────────────────────────────────────────────────────


def plot_risk_profile_interactive(result: Any) -> Any:
    """Interactive two-panel chart: outcome distribution + KPI panel.

    Mirrors :func:`plot_risk_profile` using Plotly for hover & zoom.

    Parameters
    ----------
    result:
        A fully computed ``SimulationResult`` (must contain
        ``results_array``, ``expected_value``, ``var_95``, ``p95``).

    Returns
    -------
    plotly.graph_objects.Figure
    """
    _require_plotly()
    assert go is not None  # guaranteed by _require_plotly()
    assert make_subplots is not None

    scenarios = result.results_array
    expected = float(result.expected_value)
    var95 = float(result.var_95)
    best = float(result.p95)
    feature_name = getattr(result, "feature_name", "Feature")

    # noinspection PyCallingNonCallableInspection
    fig = make_subplots(
        rows=1,
        cols=2,
        column_widths=[0.72, 0.28],
        subplot_titles=("Outcome Distribution", "Key Decision Metrics"),
        specs=[[{"type": "xy"}, {"type": "table"}]],
    )

    # ── Left panel: histogram ─────────────────────────────────────────
    fig.add_trace(
        go.Histogram(
            x=scenarios,
            nbinsx=60,
            marker_color=palette["primary"],
            marker_line_color=_BG,
            marker_line_width=0.6,
            opacity=0.82,
            name="Scenario outcomes",
            hovertemplate="Value: \u20ac%{x:,.0f}<br>Count: %{y}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # Downside shading — explicitly scoped to x/y axis 1
    fig.add_shape(
        type="rect",
        xref="x",
        yref="paper",
        x0=float(scenarios.min()),
        x1=var95,
        y0=0,
        y1=1,
        fillcolor=palette["danger"],
        opacity=0.12,
        layer="below",
        line_width=0,
    )

    # Vertical lines — use add_shape with xref="x", yref="paper" to stay in xy subplot
    for x_val, color, dash, label in [
        (
            var95,
            palette["danger"],
            "dash",
            f"Business Value Floor 95: \u20ac{var95:,.0f}",
        ),
        (
            expected,
            palette["secondary"],
            "solid",
            f"{EXPECTED_BUSINESS_VALUE_LABEL}: \u20ac{expected:,.0f}",
        ),
        (best, palette["primary"], "dot", f"P95: \u20ac{best:,.0f}"),
    ]:
        fig.add_shape(
            type="line",
            xref="x",
            yref="paper",
            x0=x_val,
            x1=x_val,
            y0=0,
            y1=1,
            line={"color": color, "dash": dash, "width": 2},
        )
        fig.add_annotation(
            x=x_val,
            y=1,
            xref="x",
            yref="paper",
            text=label,
            showarrow=False,
            font={"size": 9, "color": color},
            textangle=-90,
            xanchor="left",
        )

    # ── Right panel: KPI table ────────────────────────────────────────
    kpis = [
        (EXPECTED_BUSINESS_VALUE_LABEL, f"\u20ac{expected:,.0f}", palette["secondary"]),
        ("Business Value Floor 95", f"\u20ac{var95:,.0f}", palette["danger"]),
        ("P95 (Upside)", f"\u20ac{best:,.0f}", palette["primary"]),
    ]
    fig.add_trace(
        go.Table(
            header={
                "values": ["<b>Metric</b>", "<b>Value</b>"],
                "fill_color": _NEUTRAL,
                "font": {"size": 12, "color": _BG},
                "align": "left",
                "height": 28,
            },
            cells={
                "values": [
                    [k for k, _, _ in kpis],
                    [v for _, v, _ in kpis],
                ],
                "fill_color": [
                    [_BG] * len(kpis),
                    [c for _, _, c in kpis],
                ],
                "font": {"size": 11, "color": [_NEUTRAL, _BG]},
                "align": "left",
                "height": 28,
            },
        ),
        row=1,
        col=2,
    )

    fig.update_layout(
        title_text=f"Decision Profile \u2014 {feature_name}",
        title_font_size=15,
        showlegend=False,
        height=400,
        margin={"t": 60, "b": 40, "l": 40, "r": 20},
        paper_bgcolor=_BG,
        plot_bgcolor=_SURFACE,
    )
    fig.update_xaxes(title_text=BUSINESS_VALUE_EURO_AXIS, row=1, col=1)
    fig.update_yaxes(title_text="Frequency", row=1, col=1)

    return fig


# ── Feature Distributions ─────────────────────────────────────────────────────


def plot_feature_distributions_interactive(
    results: list[Any],
    *,
    title: str = "Feature Business Value Distributions",
    colors: list[str] | None = None,
) -> Any:
    """Interactive overlapping distribution chart for multiple features.

    Mirrors :func:`plot_feature_distributions` using Plotly.

    Parameters
    ----------
    results:
        List of ``SimulationResult`` objects.
    title:
        Chart title.
    colors:
        Optional list of palette-derived hex colours (one per feature).

    Returns
    -------
    plotly.graph_objects.Figure
    """
    _require_plotly()
    assert go is not None  # guaranteed by _require_plotly()

    palette_cycle = _extra_colors()

    fig = go.Figure()

    for idx, result in enumerate(results):
        color = (
            colors[idx]
            if colors and idx < len(colors)
            else palette_cycle[idx % len(palette_cycle)]
        )
        feature_name = getattr(result, "feature_name", f"Feature {idx + 1}")
        scenarios = result.results_array
        var95 = float(result.var_95)

        fig.add_trace(
            go.Histogram(
                x=scenarios,
                nbinsx=50,
                name=feature_name,
                marker_color=color,
                opacity=0.55,
                hovertemplate=(
                    f"<b>{feature_name}</b><br>"
                    "Value: \u20ac%{x:,.0f}<br>"
                    "Count: %{y}"
                    "<extra></extra>"
                ),
            )
        )

        # Downside floor line per feature
        fig.add_vline(
            x=var95,
            line_color=color,
            line_dash="dash",
            line_width=1.5,
            annotation_text=f"Business Value Floor {feature_name}: \u20ac{var95:,.0f}",
            annotation_font_size=9,
            annotation_font_color=color,
        )

    fig.update_layout(
        barmode="overlay",
        title_text=title,
        title_font_size=15,
        xaxis_title=BUSINESS_VALUE_EURO_AXIS,
        yaxis_title="Frequency",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.25,
            "xanchor": "center",
            "x": 0.5,
        },
        height=420,
        margin={"t": 60, "b": 80, "l": 50, "r": 20},
        paper_bgcolor=_BG,
        plot_bgcolor=_SURFACE,
    )

    return fig


# ── Multi-Year Fan Chart ──────────────────────────────────────────────────────


def plot_multi_year_fan_interactive(
    multi_year_results: list[Any],
    *,
    title: str = "3-Year Simulated Business Value",
    colors: list[str] | None = None,
    features: list[Any] | None = None,
) -> Any:
    """Interactive fan chart with confidence bands per year.

    Mirrors :func:`plot_multi_year_fan` using Plotly.

    Parameters
    ----------
    multi_year_results:
        List of ``MultiYearResult`` objects (one per feature).
    title:
        Chart title.
    colors:
        Optional list of hex colour strings.
    features:
        Optional list of ``Feature`` objects for installment overlay.
    colors:
        Optional list of palette-derived hex colours.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    _require_plotly()
    assert go is not None  # guaranteed by _require_plotly()
    assert make_subplots is not None

    n = len(multi_year_results)
    palette_cycle = _extra_colors()

    subplot_titles = [
        getattr(myr, "feature_name", f"Feature {idx + 1}")
        for idx, myr in enumerate(multi_year_results)
    ]

    # noinspection PyCallingNonCallableInspection

    # noinspection PyCallingNonCallableInspection
    fig = make_subplots(
        rows=1,
        cols=n,
        subplot_titles=subplot_titles,
        shared_yaxes=False,
    )

    for idx, myr in enumerate(multi_year_results):
        col = idx + 1
        color = _feature_panel_color(idx, colors, palette_cycle)
        feat_name = subplot_titles[idx]

        yrs = [yr.year for yr in myr.years]
        expected = [float(yr.expected) for yr in myr.years]
        floor = [float(yr.var_95) for yr in myr.years]
        ceiling = [float(yr.p95) for yr in myr.years]

        first = idx == 0

        # Confidence band (fill between floor and ceiling)
        fig.add_trace(
            go.Scatter(
                x=yrs + yrs[::-1],
                y=ceiling + floor[::-1],
                fill="toself",
                fillcolor=color,
                opacity=0.18,
                line={"color": "rgba(0,0,0,0)"},
                name=f"{feat_name} \u2014 P5\u2013P95 band",
                showlegend=first,
                hoverinfo="skip",
            ),
            row=1,
            col=col,
        )

        # Business value floor
        fig.add_trace(
            go.Scatter(
                x=yrs,
                y=floor,
                mode=LINES_AND_MARKERS_MODE,
                line={"color": color, "dash": "dash", "width": 1.5},
                marker={"size": 6, "symbol": "diamond"},
                name="Business Value Floor 95",
                showlegend=first,
                hovertemplate=(
                    "Year %{x}<br>Business value floor: \u20ac%{y:,.0f}<extra></extra>"
                ),
            ),
            row=1,
            col=col,
        )

        # Expected line
        fig.add_trace(
            go.Scatter(
                x=yrs,
                y=expected,
                mode=LINES_AND_MARKERS_MODE,
                line={"color": color, "width": 2.5},
                marker={"size": 8},
                name="Expected",
                showlegend=first,
                hovertemplate="Year %{x}<br>Expected: \u20ac%{y:,.0f}<extra></extra>",
            ),
            row=1,
            col=col,
        )

        # Ceiling (P95)
        fig.add_trace(
            go.Scatter(
                x=yrs,
                y=ceiling,
                mode=LINES_AND_MARKERS_MODE,
                line={"color": color, "dash": "dot", "width": 1.5},
                marker={"size": 6, "symbol": "triangle-up"},
                name="Ceiling (P95)",
                showlegend=first,
                hovertemplate="Year %{x}<br>Ceiling: \u20ac%{y:,.0f}<extra></extra>",
            ),
            row=1,
            col=col,
        )

        # Installment overlay
        if features and idx < len(features):
            feat = features[idx]
            dep_per_year = float(getattr(feat, "annual_installment", 0.0))
            dep_years = int(getattr(feat, "installment_years", 1))
            if dep_per_year > 0:
                inst_vals = [dep_per_year if yr <= dep_years else 0.0 for yr in yrs]
                fig.add_trace(
                    go.Scatter(
                        x=yrs,
                        y=inst_vals,
                        mode="lines",
                        line={
                            "color": palette["danger"],
                            "dash": "dashdot",
                            "width": 2,
                        },
                        name="Annual Installment",
                        showlegend=first,
                        hovertemplate="Year %{x}<br>Installment: \u20ac%{y:,.0f}<extra></extra>",
                    ),
                    row=1,
                    col=col,
                )

        fig.update_xaxes(title_text="Year", row=1, col=col, dtick=1)
        fig.update_yaxes(
            title_text="Business Value (\u20ac)" if col == 1 else "",
            tickformat=",.0f",
            tickprefix="\u20ac",
            row=1,
            col=col,
        )

    fig.update_layout(
        title_text=title,
        title_font_size=15,
        height=420,
        margin={"t": 70, "b": 60, "l": 60, "r": 20},
        paper_bgcolor=_BG,
        plot_bgcolor=_SURFACE,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.22,
            "xanchor": "center",
            "x": 0.5,
        },
    )

    return fig


__all__ = [
    "plot_feature_distributions_interactive",
    "plot_multi_year_fan_interactive",
    "plot_risk_profile_interactive",
]
