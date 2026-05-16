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

"""Simulation result plotting: static (Matplotlib) and interactive (Plotly)."""

from __future__ import annotations

import logging

from fhs.core.model import SimulationResult
from fhs.presentation.notebook import COLORS

# noinspection PyProtectedMember
from fhs.presentation.notebook.charts._helpers import _place_bottom_legend

logger = logging.getLogger("fhs.plotting.simulation")


def plot_results(
    result: SimulationResult,
    risk_analysis: dict | None = None,
    interactive: bool = False,
) -> None:
    """
    Plot simulation results with box plot and risk metrics.

    Args:
        result: Simulation result to plot
        risk_analysis: Optional risk analysis to include in the plot
        interactive: If True, use Plotly for interactive plots; otherwise use Matplotlib
    """
    if not result.results:
        logger.warning(f"No simulation results to plot for '{result.feature_name}'")
        return

    if interactive:
        _plot_results_plotly(result, risk_analysis)
    else:
        _plot_results_matplotlib(result, risk_analysis)


def _plot_results_matplotlib(
    result: SimulationResult, risk_analysis: dict | None = None
) -> None:
    """Static matplotlib plotting."""
    import matplotlib

    # Use a non-interactive backend so tests and headless environments don't crash
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12, 10), gridspec_kw={"height_ratios": [1, 3]}
    )

    # 1. Box Plot (Top)
    ax1.boxplot(
        result.results,
        orientation="horizontal",
        patch_artist=True,
        boxprops={"facecolor": COLORS.primary, "alpha": 0.35},
        medianprops={"color": COLORS.primary, "linewidth": 2},
    )
    ax1.set_title(
        f"Risk Distribution for {result.feature_name}",
        fontsize=16,
        fontweight="bold",
        color=COLORS.neutral,
    )
    ax1.set_xlabel("Value", fontsize=13, color=COLORS.neutral)
    ax1.set_yticks([])
    ax1.grid(True, alpha=0.3)

    # 2. Histogram (Bottom)
    ax2.hist(
        result.results,
        bins=50,
        alpha=0.8,
        color=COLORS.primary,
        edgecolor=COLORS.background,
        density=True,
    )

    ax2.axvline(
        result.mean,
        color=COLORS.secondary,
        linestyle="--",
        linewidth=2,
        label=f"Mean: {result.mean:.2f}",
    )
    ax2.axvline(
        result.median,
        color=COLORS.primary,
        linestyle="-",
        linewidth=2,
        label=f"Median: {result.median:.2f}",
    )

    if risk_analysis:
        if "var_95" in risk_analysis:
            ax2.axvline(
                risk_analysis["var_95"],
                color=COLORS.warning,
                linestyle="--",
                linewidth=2,
                label=f"VaR 95%: {risk_analysis['var_95']:.2f}",
            )
        if "var_99" in risk_analysis:
            ax2.axvline(
                risk_analysis["var_99"],
                color=COLORS.danger,
                linestyle="--",
                linewidth=2,
                label=f"VaR 99%: {risk_analysis['var_99']:.2f}",
            )
        if "confidence_interval" in risk_analysis:
            ci_low, ci_high = risk_analysis["confidence_interval"]
            ax2.axvspan(
                ci_low,
                ci_high,
                alpha=0.15,
                color=COLORS.neutral,
                label=f"95% CI: [{ci_low:.0f}, {ci_high:.0f}]",
            )

    ax2.set_xlabel("Conversion Value", fontsize=12)
    ax2.set_ylabel("Probability Density", fontsize=12)
    ax2.grid(True, alpha=0.3)
    handles, labels = ax2.get_legend_handles_labels()
    legend_bottom = 0.0
    if handles:
        legend_bottom = _place_bottom_legend(
            fig,
            handles,
            labels,
            max_cols=3,
            fontsize=9.5,
        )

    plt.tight_layout(rect=(0, 0.02, 1, 1))
    fig.subplots_adjust(bottom=max(0.12, legend_bottom))
    plt.show()


def _plot_results_plotly(
    result: SimulationResult, risk_analysis: dict | None = None
) -> None:
    """Interactive Plotly plotting."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=2,
        cols=1,
        row_heights=[0.25, 0.75],
        subplot_titles=(
            f"Risk Distribution for {result.feature_name}",
            "Distribution Histogram with Risk Metrics",
        ),
        vertical_spacing=0.12,
    )

    fig.add_trace(
        go.Box(
            x=result.results,
            name="Distribution",
            marker_color=COLORS.primary,
            boxmean="sd",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Histogram(
            x=result.results,
            nbinsx=50,
            name="Distribution",
            marker_color=COLORS.primary,
            opacity=0.7,
            histnorm="probability density",
        ),
        row=2,
        col=1,
    )

    shapes: list[dict] = []
    plot_annotations: list[dict] = []

    shapes.append(
        {
            "type": "line",
            "x0": result.mean,
            "x1": result.mean,
            "y0": 0,
            "y1": 1,
            "yref": "paper",
            "line": {"color": COLORS.secondary, "width": 2, "dash": "dash"},
        }
    )
    plot_annotations.append(
        {
            "x": result.mean,
            "y": 0.95,
            "yref": "paper",
            "text": f"Mean: {result.mean:.2f}",
            "showarrow": False,
            "font": {"color": COLORS.secondary},
        }
    )

    shapes.append(
        {
            "type": "line",
            "x0": result.median,
            "x1": result.median,
            "y0": 0,
            "y1": 1,
            "yref": "paper",
            "line": {"color": COLORS.primary, "width": 2},
        }
    )
    plot_annotations.append(
        {
            "x": result.median,
            "y": 0.90,
            "yref": "paper",
            "text": f"Median: {result.median:.2f}",
            "showarrow": False,
            "font": {"color": COLORS.primary},
        }
    )

    if risk_analysis:
        # Keep VaR labels out of the histogram area on small screens by placing
        # them in the free band between the two panels.
        band_y = 0.72
        connector_px = 36
        line_gap_px = 6
        if "var_95" in risk_analysis:
            var95 = risk_analysis["var_95"]
            shapes.append(
                {
                    "type": "line",
                    "x0": var95,
                    "x1": var95,
                    "y0": 0,
                    "y1": 1,
                    "yref": "paper",
                    "line": {"color": COLORS.warning, "width": 2, "dash": "dash"},
                }
            )
            plot_annotations.append(
                {
                    "x": var95,
                    "xref": "x2",
                    "y": band_y,
                    "yref": "paper",
                    "text": f"BVF 95%: {var95:.2f}",
                    "showarrow": True,
                    "arrowhead": 0,
                    "arrowwidth": 1.6,
                    "arrowcolor": COLORS.warning,
                    "ax": connector_px,
                    "ay": 0,
                    "standoff": line_gap_px,
                    "xanchor": "left",
                    "font": {"color": COLORS.warning},
                    "bgcolor": COLORS.background,
                    "bordercolor": COLORS.warning,
                    "borderwidth": 1,
                    "borderpad": 4,
                }
            )

        if "var_99" in risk_analysis:
            var99 = risk_analysis["var_99"]
            shapes.append(
                {
                    "type": "line",
                    "x0": var99,
                    "x1": var99,
                    "y0": 0,
                    "y1": 1,
                    "yref": "paper",
                    "line": {"color": COLORS.danger, "width": 2, "dash": "dash"},
                }
            )
            plot_annotations.append(
                {
                    "x": var99,
                    "xref": "x2",
                    "y": band_y,
                    "yref": "paper",
                    "text": f"VaR 99%: {var99:.2f}",
                    "showarrow": True,
                    "arrowhead": 0,
                    "arrowwidth": 1.6,
                    "arrowcolor": COLORS.danger,
                    "ax": -connector_px,
                    "ay": 0,
                    "standoff": line_gap_px,
                    "xanchor": "right",
                    "font": {"color": COLORS.danger},
                    "bgcolor": COLORS.background,
                    "bordercolor": COLORS.danger,
                    "borderwidth": 1,
                    "borderpad": 4,
                }
            )

    fig.update_layout(
        shapes=shapes,
        annotations=plot_annotations,
        showlegend=False,
        height=800,
        title_text=f"Risk Analysis: {result.feature_name}",
        title_font_size=20,
        font={"color": COLORS.neutral, "size": 14},
        margin={"t": 120, "b": 80, "l": 70, "r": 40},
    )

    fig.update_xaxes(title_text="Value", row=1, col=1)
    fig.update_xaxes(title_text="Conversion Value", row=2, col=1)
    fig.update_yaxes(title_text="Probability Density", row=2, col=1)
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)

    fig.show()


def plot_comparison(comparison) -> None:
    """
    Plot comparison of multiple features.

    Args:
        comparison: Feature comparison result from compare_features (dict or list)
    """
    import matplotlib

    # Force headless-friendly backend to avoid GUI dependencies during tests
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not comparison:
        plt.figure()
        plt.title("No features to compare")
        plt.show()
        return

    comparison_dict = {}
    if isinstance(comparison, list):
        for item in comparison:
            feature = item["feature"]
            feature_name = feature.name
            comparison_dict[feature_name] = {
                "simulation_result": item["simulation"],
                "risk_analysis": item["risk"],
            }
    else:
        comparison_dict = comparison

    _fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 7.2))

    feature_names = list(comparison_dict.keys())
    means = [comparison_dict[name]["risk_analysis"]["mean"] for name in feature_names]

    var95 = []
    for name in feature_names:
        risk = comparison_dict[name]["risk_analysis"]
        if "var_95" in risk:
            var95.append(risk["var_95"])
        else:
            var95.append(risk.get("mean", 0) * 0.8)

    # 1. Expected Value Comparison
    ax1.bar(feature_names, means, color=COLORS.primary)
    ax1.set_title(
        "Expected Value Comparison",
        fontsize=16,
        fontweight="bold",
        color=COLORS.neutral,
    )
    ax1.set_ylabel("Expected Value", fontsize=13, color=COLORS.neutral)
    ax1.grid(True, alpha=0.25, color=COLORS.grid)
    plt.setp(
        ax1.xaxis.get_majorticklabels(), rotation=24, ha="right", color=COLORS.neutral
    )
    plt.setp(ax1.yaxis.get_majorticklabels(), color=COLORS.neutral)

    # 2. Risk Distribution Comparison (Box Plot)
    box_data = [
        comparison_dict[name]["simulation_result"].results for name in feature_names
    ]
    ax2.boxplot(
        box_data,
        tick_labels=feature_names,
        patch_artist=True,
        boxprops={"facecolor": COLORS.primary, "alpha": 0.35},
        medianprops={"color": COLORS.primary, "linewidth": 2},
    )
    ax2.set_title(
        "Risk Distribution Comparison",
        fontsize=16,
        fontweight="bold",
        color=COLORS.neutral,
    )
    ax2.set_ylabel("Simulated Value", fontsize=13, color=COLORS.neutral)
    ax2.grid(True, alpha=0.25, color=COLORS.grid)
    plt.setp(
        ax2.xaxis.get_majorticklabels(), rotation=24, ha="right", color=COLORS.neutral
    )
    plt.setp(ax2.yaxis.get_majorticklabels(), color=COLORS.neutral)

    # 3. VaR values
    ax3.bar(feature_names, var95, color=COLORS.danger)
    ax3.set_title(
        "VaR (95%) Comparison", fontsize=16, fontweight="bold", color=COLORS.neutral
    )
    ax3.set_ylabel("Value at Risk (95%)", fontsize=13, color=COLORS.neutral)
    ax3.grid(True, alpha=0.25, color=COLORS.grid)
    plt.setp(
        ax3.xaxis.get_majorticklabels(), rotation=24, ha="right", color=COLORS.neutral
    )
    plt.setp(ax3.yaxis.get_majorticklabels(), color=COLORS.neutral)

    plt.tight_layout(pad=2.0)
    plt.show()
