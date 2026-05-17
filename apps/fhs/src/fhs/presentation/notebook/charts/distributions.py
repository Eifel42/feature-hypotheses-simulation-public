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

"""Distribution charts: risk profile, uncertainty comparison, feature & portfolio."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from ..styling import (
    FIG,
    HIST_ALPHA,
    HIST_BINS,
    HIST_EDGE_COLOR,
    HIST_EDGE_WIDTH,
    palette,
)
from ._helpers import (
    _annotate_vertical_callouts,
    _apply_axis_style,
    _cycle_colors,
    _place_bottom_legend,
    _show_fig,
)

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from fhs.core.model import Feature, SimulationResult

DOWNSIDE_ZONE_LABEL = "Downside zone (< BVF 95%)"
CONVERSION_RATE_LABEL = "Conversion Rate"
BUSINESS_VALUE_EUR_LABEL = "Business Value (EUR)"
ANNUAL_INSTALLMENT_LABEL = "Annual Installment"


def _distribution_callouts(
    *,
    var95_k: float,
    expected_k: float,
    p95_k: float,
) -> list[tuple[float, str, str]]:
    return [
        (
            var95_k,
            f"FLOOR VaR95\n{var95_k:.0f}k",
            palette["danger"],
        ),
        (
            expected_k,
            f"MEAN\n{expected_k:.0f}k",
            palette["neutral"],
        ),
        (
            p95_k,
            f"UPSIDE P95\n{p95_k:.0f}k",
            palette["secondary"],
        ),
    ]


# ── Risk-Profile Dashboard ────────────────────────────────────────────


def plot_risk_profile(result: SimulationResult) -> Figure:
    """Two-panel chart: outcome distribution (left) + KPI panel (right).

    Parameters
    ----------
    result:
        A fully computed ``SimulationResult`` (must contain
        ``results_array``, ``expected_value``, ``var_95``, ``p95``).

    Returns
    -------
    matplotlib.figure.Figure
    """
    scenarios = result.results_array
    expected = result.expected_value
    var95 = result.var_95
    best = result.p95

    fig, (ax_dist, ax_kpi) = plt.subplots(
        1,
        2,
        figsize=FIG.medium,
        gridspec_kw={"width_ratios": [3, 1.35]},
    )

    # ── Left: distribution histogram ─────────────────────────────────
    ax_dist.hist(
        scenarios,
        bins=HIST_BINS + 10,
        color=palette["primary"],
        alpha=HIST_ALPHA,
        edgecolor=HIST_EDGE_COLOR,
        linewidth=HIST_EDGE_WIDTH,
        label="Scenario outcomes",
    )
    ax_dist.axvspan(
        scenarios.min(),
        var95,
        alpha=0.12,
        color=palette["danger"],
        zorder=0,
        lw=0,
        label=DOWNSIDE_ZONE_LABEL,
    )
    ax_dist.axvline(
        var95,
        color=palette["danger"],
        linewidth=1.8,
        linestyle="--",
        zorder=5,
        label=f"Business Value Floor ({var95:,.0f})",
    )
    ax_dist.axvline(
        expected,
        color=palette["neutral"],
        linewidth=1.8,
        zorder=5,
        label=f"Expected ({expected:,.0f})",
    )
    ax_dist.axvline(
        best,
        color=palette["secondary"],
        linewidth=1.2,
        linestyle=":",
        zorder=4,
        alpha=0.8,
        label=f"P95 ({best:,.0f})",
    )
    y_min, y_max = ax_dist.get_ylim()
    y_span = max(y_max - y_min, 1e-9)
    side_callouts = [
        (
            var95,
            "Downside Floor\nBVF 95%",
            palette["danger"],
            -58,
            0.84,
        ),
        (
            expected,
            "Expected Value",
            palette["neutral"],
            54,
            0.70,
        ),
        (
            best,
            "Upside Potential\nP95",
            palette["secondary"],
            58,
            0.84,
        ),
    ]
    for x_val, text, color, x_offset, y_frac in side_callouts:
        y_anchor = y_min + y_span * y_frac
        ax_dist.annotate(
            text,
            xy=(x_val, y_anchor),
            xycoords="data",
            xytext=(x_offset, 0),
            textcoords="offset points",
            ha="right" if x_offset < 0 else "left",
            va="center",
            fontsize=9,
            linespacing=1.35,
            color=color,
            fontweight="bold",
            zorder=8,
            bbox={
                "boxstyle": "round,pad=0.32",
                "facecolor": palette["background"],
                "edgecolor": color,
                "linewidth": 1.0,
                "alpha": 0.98,
            },
            arrowprops={
                "arrowstyle": "-",
                "color": color,
                "lw": 1.2,
                "shrinkA": 6,
                "shrinkB": 4,
                "connectionstyle": "arc3,rad=0.0",
            },
        )

    ax_dist.set_title(
        "Outcome Distribution — 10,000 Scenarios",
        fontsize=12,
        fontweight="bold",
        pad=15,
    )
    ax_dist.set_xlabel("Conversions", fontsize=10, labelpad=8)
    ax_dist.set_ylabel("Scenarios", fontsize=10, labelpad=8)
    _apply_axis_style(ax_dist, grid_axis="y")

    # ── Right: KPI panel ─────────────────────────────────────────────
    ax_kpi.axis("off")
    kpi_data = [
        (
            "Best Case (P95)",
            f"{best:,.0f}",
            palette["secondary"],
            "95th percentile: only 5% are higher",
        ),
        (
            "Expected",
            f"{expected:,.0f}",
            palette["neutral"],
            "Average across all scenarios",
        ),
        (
            "BVF 95% (Floor)",
            f"{var95:,.0f}",
            palette["danger"],
            "5th percentile: only 5% are lower",
        ),
    ]
    ax_kpi.set_xlim(0, 1)
    ax_kpi.set_ylim(0, 1)
    y_positions = [0.86, 0.54, 0.22]
    for i, (lbl, val, col, note) in enumerate(kpi_data):
        y = y_positions[i]
        ax_kpi.text(
            0.5,
            y,
            val,
            transform=ax_kpi.transAxes,
            ha="center",
            va="bottom",
            fontsize=24,
            fontweight="bold",
            color=col,
        )
        ax_kpi.text(
            0.5,
            y - 0.065,
            lbl,
            transform=ax_kpi.transAxes,
            ha="center",
            va="top",
            fontsize=10,
            color=palette["neutral"],
            fontweight="semibold",
        )
        ax_kpi.text(
            0.5,
            y - 0.125,
            note,
            transform=ax_kpi.transAxes,
            ha="center",
            va="top",
            fontsize=10,
            color=palette["neutral"],
        )
        if i < len(kpi_data) - 1:
            sep_y = (y + y_positions[i + 1]) / 2 - 0.01
            ax_kpi.plot(
                [0.1, 0.9],
                [sep_y, sep_y],
                color=palette["border"],
                linewidth=0.8,
                transform=ax_kpi.transAxes,
            )
    ax_kpi.set_title("Key Numbers", fontsize=12, fontweight="bold", pad=14)

    # ── Layout: legend centered below x-axis ─────────────────────────
    plt.tight_layout(pad=2.0, w_pad=2.4, rect=(0, 0.10, 1, 0.95))
    handles, labels = ax_dist.get_legend_handles_labels()
    legend_bottom = _place_bottom_legend(
        fig,
        handles,
        labels,
        max_cols=3,
        fontsize=8.5,
    )
    fig.subplots_adjust(bottom=max(0.20, legend_bottom + 0.01), top=0.90)
    _show_fig(fig)
    return fig


# ── Uncertainty Comparison ────────────────────────────────────────────


def plot_uncertainty_comparison(
    feature: Feature,
    *,
    levels: tuple[float, ...] = (0.10, 0.30, 0.50),
    n_scenarios: int = 10_000,
    seed: int = 42,
) -> Figure:
    """Three-panel chart showing identical feature at different uncertainty levels.

    Parameters
    ----------
    feature:
        Base ``Feature`` — *uncertainty* is overridden per panel.
    levels:
        Uncertainty values for Low / Medium / High.
    n_scenarios:
        Number of Monte Carlo draws per panel.
    seed:
        Random seed for reproducibility.
    """
    from fhs.application.calculation_service import FeatureCalculationService
    from fhs.core.model import Feature as _Feature

    colors = [palette["secondary"], palette["warning"], palette["danger"]]
    labels = ["Low", "Medium", "High"]

    fig, axes = plt.subplots(1, len(levels), figsize=FIG.wide)
    if not hasattr(axes, "__len__"):
        axes = [axes]

    all_ranges: list[float] = []
    for idx, (ax, unc, color, label) in enumerate(
        zip(axes, levels, colors, labels, strict=False)
    ):
        f = _Feature(
            name=feature.name,
            expected_users=feature.expected_users,
            conversion_rate=feature.conversion_rate,
            uncertainty=unc,
        )
        r = FeatureCalculationService.simulate_feature(
            f, scenarios=n_scenarios, seed=seed
        )
        s = r.results_array

        ax.hist(
            s,
            bins=HIST_BINS,
            color=color,
            alpha=HIST_ALPHA,
            edgecolor=HIST_EDGE_COLOR,
            linewidth=HIST_EDGE_WIDTH,
        )
        ax.axvline(
            r.expected_value,
            color=palette["neutral"],
            linewidth=1.5,
            label="Expected" if idx == 0 else "_nolegend_",
        )
        ax.axvline(
            r.var_95,
            color=palette["danger"],
            linewidth=1.5,
            linestyle="--",
            label="VaR 95%" if idx == 0 else "_nolegend_",
        )

        spread = r.p95 - r.p5
        all_ranges.append(spread)
        ax.set_title(
            f"{label} Uncertainty ({unc:.2f})\nOutcome range: {spread:,.0f}",
            fontsize=11,
            pad=10,
        )
        ax.set_xlabel("Conversions", labelpad=8)
        _apply_axis_style(ax, grid_axis="y")

    axes[0].set_ylabel("Scenarios", labelpad=8)
    fig.suptitle(
        "Same Feature \u2014 Three Uncertainty Levels",
        fontsize=15,
        fontweight="bold",
        y=0.98,
    )
    plt.tight_layout(pad=2.5, rect=(0, 0.02, 1, 0.94))
    handles, labels = axes[0].get_legend_handles_labels()
    legend_bottom = _place_bottom_legend(
        fig,
        handles,
        labels,
        max_cols=2,
        fontsize=9.0,
    )
    fig.subplots_adjust(bottom=max(0.18, legend_bottom + 0.01))
    _show_fig(fig)

    # Attach insight text for the notebook to display
    if len(all_ranges) >= 3 and all_ranges[2] > 0:
        pct = (1 - all_ranges[0] / all_ranges[2]) * 100
        fig._fhs_insight = (
            f"Reducing uncertainty from {levels[-1]:.0%} to {levels[0]:.0%} "
            f"shrinks the outcome range by <b>{pct:.0f}%</b>. "
            "User testing and market research do not just inform decisions — "
            "they <i>narrow the range of possible outcomes</i>."
        )

    return fig


# ── Distribution Guide Helpers (T01) ──────────────────────────────────


def plot_beta_sample_size_effect(
    *,
    trials: tuple[tuple[str, int, int], ...] = (
        ("Low Confidence\n25 trials", 2, 23),
        ("Medium Confidence\n200 trials", 16, 184),
        ("High Confidence\n3,000 trials", 240, 2760),
    ),
    n_samples: int = 10_000,
    seed: int = 42,
    title: str = "Beta Distribution: More Data = Narrower Estimate",
) -> Figure:
    """Three-panel Beta chart showing confidence shrink with more observations."""
    rng = np.random.default_rng(seed)
    colors = [palette["danger"], palette["warning"], palette["secondary"]]

    fig, axes = plt.subplots(1, len(trials), figsize=FIG.wide)
    if not hasattr(axes, "__len__"):
        axes = [axes]
    fig.suptitle(title, fontsize=14, fontweight="bold", y=0.995)

    for ax, (trial_label, alpha, beta_param), color in zip(
        axes, trials, colors, strict=False
    ):
        samples = rng.beta(alpha, beta_param, n_samples)
        mean_val = float(np.mean(samples))
        ci_lo, ci_hi = np.percentile(samples, [2.5, 97.5])

        ax.hist(
            samples,
            bins=HIST_BINS,
            alpha=0.60,
            color=color,
            edgecolor=HIST_EDGE_COLOR,
            linewidth=HIST_EDGE_WIDTH,
            density=True,
        )
        ax.axvline(
            mean_val,
            color=palette["neutral"],
            linewidth=1.5,
            label=f"Mean: {mean_val:.3f}",
        )
        ax.axvspan(ci_lo, ci_hi, alpha=0.12, color=color, zorder=0)
        ax.set_title(
            f"{trial_label}\na={alpha}, b={beta_param}\n95% CI: [{ci_lo:.3f}, {ci_hi:.3f}]",
            fontsize=10,
            pad=10,
        )
        ax.set_xlabel(CONVERSION_RATE_LABEL, labelpad=8)
        _apply_axis_style(ax, grid_axis="y")

    axes[0].set_ylabel("Density", labelpad=8)
    handles, labels = axes[0].get_legend_handles_labels()
    legend_bottom = _place_bottom_legend(
        fig,
        handles,
        labels,
        max_cols=2,
        fontsize=9.0,
    )
    fig.subplots_adjust(bottom=max(0.20, legend_bottom + 0.01), top=0.80)
    _show_fig(fig)
    return fig


def plot_beta_vs_normal_boxplot(
    *,
    mean_rate: float = 0.08,
    uncertainty: float = 0.40,
    n_samples: int = 10_000,
    seed: int = 42,
    title: str | None = None,
) -> tuple[Figure, dict[str, float]]:
    """Histogram + boxplot comparison for Normal(clipped) vs Beta.

    Returns
    -------
    tuple[Figure, dict[str, float]]
        Figure and summary metrics for notebook info text.
    """
    from fhs import DEFAULT_CONFIG, BetaParameters

    rng = np.random.default_rng(seed)
    sigma_range = DEFAULT_CONFIG.UNCERTAINTY_SIGMA_RANGE
    std_dev = mean_rate * uncertainty / sigma_range

    raw_normal = rng.normal(mean_rate, std_dev, n_samples)
    normal_clipped = np.clip(raw_normal, 0.0, 1.0)

    params = BetaParameters.from_mean_uncertainty(
        mean=mean_rate, uncertainty=uncertainty
    )
    beta_samples = stats.beta.rvs(
        params.alpha, params.beta, size=n_samples, random_state=rng
    )

    raw_for_clip_check = rng.normal(mean_rate, std_dev, 100_000)
    clipped_pct = float((raw_for_clip_check < 0.0).mean() * 100.0)

    fig, axes = plt.subplots(1, 2, figsize=FIG.medium)

    axes[0].hist(
        normal_clipped,
        bins=HIST_BINS,
        alpha=0.5,
        color=palette["info"],
        label=f"Normal (clipped)  μ={float(np.mean(normal_clipped)):.4f}",
        edgecolor=HIST_EDGE_COLOR,
        linewidth=HIST_EDGE_WIDTH,
        density=True,
    )
    axes[0].hist(
        beta_samples,
        bins=HIST_BINS,
        alpha=0.5,
        color=palette["secondary"],
        label=f"Beta(α={params.alpha:.1f}, β={params.beta:.1f})  μ={float(np.mean(beta_samples)):.4f}",
        edgecolor=HIST_EDGE_COLOR,
        linewidth=HIST_EDGE_WIDTH,
        density=True,
    )
    axes[0].axvline(
        mean_rate,
        color=palette["neutral"],
        linewidth=2,
        linestyle="--",
        label=f"True mean ({mean_rate:.0%})",
    )
    axes[0].set_title(
        title
        or (
            f"8% rate at {uncertainty:.0%} uncertainty\n"
            f"Normal clips {clipped_pct:.1f}% of samples"
        )
    )
    axes[0].set_xlabel(CONVERSION_RATE_LABEL, labelpad=8)
    axes[0].set_ylabel("Density", labelpad=8)
    _apply_axis_style(axes[0], grid_axis="y")

    bp = axes[1].boxplot(
        [normal_clipped, beta_samples],
        tick_labels=[
            "Normal\n(clipped)",
            f"Beta\n(α={params.alpha:.1f}, β={params.beta:.1f})",
        ],
        patch_artist=True,
        widths=0.5,
    )
    box_colors = [palette["info"], palette["secondary"]]
    for patch, color in zip(bp["boxes"], box_colors, strict=False):
        patch.set_facecolor(color)
        patch.set_alpha(0.5)
    axes[1].axhline(
        mean_rate,
        color=palette["neutral"],
        linewidth=1.5,
        linestyle="--",
        label=f"True mean ({mean_rate:.0%})",
    )
    axes[1].set_title("Spread Comparison")
    axes[1].set_ylabel(CONVERSION_RATE_LABEL, labelpad=8)
    axes[1].legend()
    _apply_axis_style(axes[1], grid_axis="y")

    handles, labels = axes[0].get_legend_handles_labels()
    legend_bottom = _place_bottom_legend(
        fig,
        handles,
        labels,
        max_cols=3,
        fontsize=8.8,
    )
    fig.subplots_adjust(bottom=max(0.22, legend_bottom), top=0.90)
    _show_fig(fig)

    summary = {
        "clipped_pct": clipped_pct,
        "alpha": float(params.alpha),
        "beta": float(params.beta),
        "normal_mean": float(np.mean(normal_clipped)),
        "beta_mean": float(np.mean(beta_samples)),
    }
    return fig, summary


def plot_distribution_risk_metric_comparison(
    *,
    mean_rate: float = 0.08,
    uncertainty: float = 0.40,
    n_users: int = 5_000,
    business_value_per_conversion: float = 150.0,
    n_samples: int = 50_000,
    seed: int = 42,
    title: str = (
        "Same Feature: 5,000 users × 8% conversion × €150 BV — "
        "Distribution Impact on Risk Metrics"
    ),
) -> tuple[Figure, dict[str, float]]:
    """Compare VaR/CVaR under Normal, Lognormal, and Beta distributions."""
    from fhs import DEFAULT_CONFIG, BetaParameters

    rng = np.random.default_rng(seed)
    sigma_range = DEFAULT_CONFIG.UNCERTAINTY_SIGMA_RANGE
    std_dev = mean_rate * uncertainty / sigma_range

    normal_conv = np.clip(rng.normal(mean_rate, std_dev, n_samples), 0.0, 1.0)

    mu_log = np.log(mean_rate) - 0.5 * (uncertainty / sigma_range) ** 2
    sigma_log = uncertainty / sigma_range
    lognormal_conv = np.clip(rng.lognormal(mu_log, sigma_log, n_samples), 0.0, 1.0)

    bp = BetaParameters.from_mean_uncertainty(mean=mean_rate, uncertainty=uncertainty)
    beta_conv = np.asarray(
        stats.beta.rvs(bp.alpha, bp.beta, size=n_samples, random_state=rng),
        dtype=float,
    )

    def _to_business_value(raw_samples: np.ndarray) -> np.ndarray:
        return raw_samples * n_users * business_value_per_conversion

    bv_normal = _to_business_value(normal_conv)
    bv_lognormal = _to_business_value(lognormal_conv)
    bv_beta = _to_business_value(beta_conv)

    fig, axes = plt.subplots(1, 3, figsize=FIG.wide)
    fig.suptitle(title, fontsize=13, fontweight="bold", y=0.995)

    plots = [
        ("Normal (clipped)", bv_normal, palette["info"]),
        ("Lognormal", bv_lognormal, palette["accent"]),
        ("Beta", bv_beta, palette["secondary"]),
    ]

    summary: dict[str, float] = {}
    for ax, (label, samples, color) in zip(axes, plots, strict=False):
        v95 = float(np.percentile(samples, 5))  # gain-based VaR 95%
        cv95 = (
            float(np.mean(samples[samples <= v95])) if np.any(samples <= v95) else v95
        )
        mean_val = float(np.mean(samples))

        ax.hist(
            samples / 1_000.0,
            bins=HIST_BINS + 10,
            alpha=0.65,
            color=color,
            edgecolor=HIST_EDGE_COLOR,
            linewidth=HIST_EDGE_WIDTH,
            density=True,
        )
        ax.axvline(
            mean_val / 1_000.0,
            color=palette["neutral"],
            linewidth=1.5,
            label=f"Mean: €{mean_val / 1000:.1f}k",
        )
        ax.axvline(
            v95 / 1_000.0,
            color=palette["danger"],
            linewidth=1.5,
            linestyle="--",
            label=f"VaR 95%: €{v95 / 1000:.1f}k",
        )
        ax.axvline(
            cv95 / 1_000.0,
            color=palette["warning"],
            linewidth=1.5,
            linestyle=":",
            label=f"CVaR 95%: €{cv95 / 1000:.1f}k",
        )
        ax.set_title(
            f"{label}\nVaR={v95 / 1000:.1f}k  CVaR={cv95 / 1000:.1f}k", fontsize=11
        )
        ax.set_xlabel("Business Value (EUR k)", labelpad=8)
        _apply_axis_style(ax, grid_axis="y")

        summary[
            f"{label.lower().replace(' ', '_').replace('(', '').replace(')', '')}_var_95"
        ] = float(v95)
        summary[
            f"{label.lower().replace(' ', '_').replace('(', '').replace(')', '')}_cvar_95"
        ] = float(cv95)

    axes[0].set_ylabel("Density", labelpad=8)
    handles, labels = axes[0].get_legend_handles_labels()
    legend_bottom = _place_bottom_legend(
        fig,
        handles,
        labels,
        max_cols=3,
        fontsize=8.8,
    )
    fig.subplots_adjust(bottom=max(0.20, legend_bottom + 0.01), top=0.80)
    _show_fig(fig)

    normal_var = summary["normal_clipped_var_95"]
    beta_var = summary["beta_var_95"]
    lognormal_var = summary["lognormal_var_95"]
    summary["max_diff_pct_normal_vs_beta"] = float(
        abs(normal_var - beta_var) / max(abs(beta_var), 1.0) * 100.0
    )
    summary["normal_var_95"] = normal_var
    summary["beta_var_95"] = beta_var
    summary["lognormal_var_95"] = lognormal_var

    return fig, summary


def plot_distribution_shape_comparison(
    *,
    mean_rate: float = 0.08,
    normal_std: float = 0.02,
    lognormal_sigma: float = 0.3,
    beta_alpha: float = 24.0,
    beta_beta: float = 276.0,
    n_samples: int = 10_000,
    seed: int = 42,
    title: str = "Same 8% Conversion Rate — Three Different Models",
) -> tuple[Figure, dict[str, float]]:
    """Three-panel distribution shape comparison used in tutorial notebooks."""
    rng = np.random.default_rng(seed)

    normal_samples = np.clip(rng.normal(mean_rate, normal_std, n_samples), 0.0, 1.0)
    lognormal_samples = np.clip(
        rng.lognormal(np.log(mean_rate), lognormal_sigma, n_samples), 0.0, 1.0
    )
    beta_samples = rng.beta(beta_alpha, beta_beta, n_samples)

    fig, axes = plt.subplots(1, 3, figsize=FIG.wide)
    # Reserve clear headroom so figure title never collides with subplot titles.
    fig.suptitle(title, fontsize=15, fontweight="bold", y=0.975)

    configs = [
        ("Normal", normal_samples, palette["info"], "Bell-shaped, symmetric"),
        ("Lognormal", lognormal_samples, palette["accent"], "Right-skewed, realistic"),
        ("Beta", beta_samples, palette["secondary"], "Bounded [0, 1] by construction"),
    ]

    summary: dict[str, float] = {}
    for ax, (name, samples, color, desc) in zip(axes, configs, strict=False):
        mean_val = float(np.mean(samples))
        p5 = float(np.percentile(samples, 5))
        p95 = float(np.percentile(samples, 95))
        spread = p95 - p5

        ax.hist(
            samples,
            bins=HIST_BINS,
            alpha=0.60,
            color=color,
            edgecolor=HIST_EDGE_COLOR,
            linewidth=HIST_EDGE_WIDTH,
            density=True,
        )
        ax.axvline(
            mean_val,
            color=palette["neutral"],
            linewidth=1.5,
            label=f"Mean: {mean_val:.3f}",
        )
        ax.axvline(
            p5,
            color=palette["danger"],
            linewidth=1.5,
            linestyle="--",
            label=f"5th: {p5:.3f}",
        )
        ax.axvline(
            p95,
            color=palette["secondary"],
            linewidth=1.0,
            linestyle=":",
            label=f"95th: {p95:.3f}",
            alpha=0.8,
        )
        ax.set_title(f"{name}\n{desc}\nRange: {spread:.3f}", fontsize=11, pad=10)
        ax.set_xlabel(CONVERSION_RATE_LABEL, labelpad=8)
        _apply_axis_style(ax, grid_axis="y")

        key = name.lower()
        summary[f"{key}_mean"] = mean_val
        summary[f"{key}_p5"] = p5
        summary[f"{key}_p95"] = p95

    axes[0].set_ylabel("Density", labelpad=8)
    handles, labels = axes[0].get_legend_handles_labels()
    legend_bottom = _place_bottom_legend(
        fig,
        handles,
        labels,
        max_cols=3,
        fontsize=8.8,
    )
    fig.subplots_adjust(
        bottom=max(0.20, legend_bottom + 0.01),
        top=0.72,
        wspace=0.28,
    )
    _show_fig(fig)

    summary["max_var5_diff_pct_normal_vs_beta"] = float(
        abs(summary["normal_p5"] - summary["beta_p5"])
        / max(summary["beta_p5"], 1e-9)
        * 100.0
    )
    # Backward-compatible aliases used by tutorial notebook info text.
    summary["var_max_diff_pct"] = summary["max_var5_diff_pct_normal_vs_beta"]
    summary["var_normal"] = summary["normal_p5"]
    summary["var_lognormal"] = summary["lognormal_p5"]
    summary["var_beta"] = summary["beta_p5"]
    return fig, summary


def plot_normal_distribution_deep_dive(
    *,
    mean_rate: float = 0.08,
    high_uncertainty: float = 0.5,
    uncertainty_levels: tuple[float, ...] = (0.1, 0.3, 0.5),
    n_samples: int = 10_000,
    seed: int = 42,
) -> tuple[Figure, dict[str, float]]:
    """Two-panel normal-distribution deep dive: clipping bias and uncertainty spread."""
    rng = np.random.default_rng(seed)

    normal_raw = rng.normal(mean_rate, mean_rate * high_uncertainty, n_samples)
    normal_clipped = np.clip(normal_raw, 0.0, 1.0)
    clipped_pct = float((normal_raw < 0.0).mean() * 100.0)

    fig, axes = plt.subplots(1, 2, figsize=FIG.medium)

    axes[0].hist(
        normal_raw,
        bins=HIST_BINS,
        alpha=0.5,
        color=palette["danger"],
        label="Raw (has negatives!)",
        edgecolor=HIST_EDGE_COLOR,
        linewidth=HIST_EDGE_WIDTH,
    )
    axes[0].hist(
        normal_clipped,
        bins=HIST_BINS,
        alpha=0.5,
        color=palette["info"],
        label="Clipped [0,1]",
        edgecolor=HIST_EDGE_COLOR,
        linewidth=HIST_EDGE_WIDTH,
    )
    axes[0].axvline(
        0.0, color=palette["neutral"], linewidth=2, linestyle="--", label="Boundary"
    )
    axes[0].set_title("Normal Clipping Bias")
    axes[0].set_xlabel("Value")
    _apply_axis_style(axes[0], grid_axis="y")

    level_colors = [palette["secondary"], palette["warning"], palette["danger"]]
    for unc, color in zip(uncertainty_levels, level_colors, strict=False):
        samples = np.clip(rng.normal(mean_rate, mean_rate * unc, n_samples), 0.0, 1.0)
        axes[1].hist(
            samples,
            bins=HIST_BINS,
            alpha=0.5,
            color=color,
            label=f"Uncertainty {unc:.0%}",
            edgecolor=HIST_EDGE_COLOR,
            linewidth=HIST_EDGE_WIDTH,
            density=True,
        )
    axes[1].set_title("Uncertainty Impact on Shape")
    axes[1].set_xlabel(CONVERSION_RATE_LABEL)
    _apply_axis_style(axes[1], grid_axis="y")

    h0, l0 = axes[0].get_legend_handles_labels()
    h1, l1 = axes[1].get_legend_handles_labels()
    legend_bottom = _place_bottom_legend(
        fig,
        h0 + h1,
        l0 + l1,
        max_cols=3,
        fontsize=8.8,
    )
    fig.subplots_adjust(bottom=max(0.20, legend_bottom), top=0.90)
    _show_fig(fig)

    return fig, {"clipped_pct": clipped_pct}


def plot_lognormal_distribution_deep_dive(
    *,
    normal_mean: float = 1_000.0,
    normal_std: float = 500.0,
    lognormal_scale: float = 800.0,
    lognormal_sigma: float = 0.5,
    n_samples: int = 10_000,
    seed: int = 42,
) -> tuple[Figure, dict[str, float]]:
    """Two-panel lognormal deep dive: business value histogram and spread boxplot."""
    rng = np.random.default_rng(seed)

    business_value_normal = rng.normal(normal_mean, normal_std, n_samples)
    business_value_lognormal = rng.lognormal(
        np.log(lognormal_scale), lognormal_sigma, n_samples
    )

    fig, axes = plt.subplots(1, 2, figsize=FIG.medium)

    normal_avg = float(np.mean(business_value_normal))
    lognormal_avg = float(np.mean(business_value_lognormal))

    axes[0].hist(
        business_value_normal,
        bins=HIST_BINS,
        alpha=0.5,
        color=palette["info"],
        label=f"Normal (mean €{normal_avg:.0f})",
        edgecolor=HIST_EDGE_COLOR,
        linewidth=HIST_EDGE_WIDTH,
    )
    axes[0].hist(
        business_value_lognormal,
        bins=HIST_BINS,
        alpha=0.5,
        color=palette["accent"],
        label=f"Lognormal (mean €{lognormal_avg:.0f})",
        edgecolor=HIST_EDGE_COLOR,
        linewidth=HIST_EDGE_WIDTH,
    )
    axes[0].set_title("Business Value per Customer")
    axes[0].set_xlabel(BUSINESS_VALUE_EUR_LABEL)
    axes[0].set_xlim(-500, 4000)
    _apply_axis_style(axes[0], grid_axis="y")

    bp = axes[1].boxplot(
        [business_value_normal, business_value_lognormal],
        tick_labels=["Normal", "Lognormal"],
        patch_artist=True,
    )
    bp["boxes"][0].set_facecolor(palette["info"])
    bp["boxes"][0].set_alpha(0.5)
    bp["boxes"][1].set_facecolor(palette["accent"])
    bp["boxes"][1].set_alpha(0.5)
    axes[1].set_title("Spread Comparison")
    axes[1].set_ylabel(BUSINESS_VALUE_EUR_LABEL)
    _apply_axis_style(axes[1], grid_axis="y")

    handles, labels = axes[0].get_legend_handles_labels()
    legend_bottom = _place_bottom_legend(
        fig,
        handles,
        labels,
        max_cols=2,
        fontsize=8.8,
    )
    fig.subplots_adjust(bottom=max(0.20, legend_bottom), top=0.90)
    _show_fig(fig)

    summary = {
        "normal_skew": float(stats.skew(business_value_normal)),
        "lognormal_skew": float(stats.skew(business_value_lognormal)),
    }
    # Backward-compatible aliases used by tutorial notebook info text.
    summary["skew_normal"] = summary["normal_skew"]
    summary["skew_lognormal"] = summary["lognormal_skew"]
    return fig, summary


# ── Per-Feature Distribution Panels (NB02, T02) ──────────────────────


def _draw_feature_distribution_panel(
    ax: Any,
    idx: int,
    label: str,
    d: dict[str, Any],
    color: str,
    divisor: float,
    unit: str,
    installment_by_feature: dict[str, float] | None,
) -> None:
    data_k = d["scenarios"] / divisor
    expected_k = d["expected"] / divisor
    var95_k = d["var95"] / divisor
    p95_k = d["p95"] / divisor

    ax.hist(
        data_k,
        bins=HIST_BINS + 10,
        color=color,
        alpha=HIST_ALPHA,
        edgecolor=HIST_EDGE_COLOR,
        linewidth=HIST_EDGE_WIDTH,
        label="Scenarios" if idx == 0 else "_nolegend_",
    )
    ax.axvspan(
        data_k.min(),
        var95_k,
        alpha=0.12,
        color=palette["danger"],
        lw=0,
        label=DOWNSIDE_ZONE_LABEL if idx == 0 else "_nolegend_",
    )
    ax.axvline(
        var95_k,
        color=palette["danger"],
        linewidth=1.6,
        linestyle="--",
        label="VaR 95%" if idx == 0 else "_nolegend_",
    )
    ax.axvline(
        expected_k,
        color=palette["neutral"],
        linewidth=1.8,
        label="Expected" if idx == 0 else "_nolegend_",
    )
    ax.axvline(
        p95_k,
        color=palette["secondary"],
        linewidth=1.2,
        linestyle=":",
        label="P95" if idx == 0 else "_nolegend_",
    )

    if installment_by_feature and label in installment_by_feature:
        dep_k = installment_by_feature[label] / divisor
        ax.axvline(
            dep_k,
            color=palette["danger"],
            linewidth=1.5,
            linestyle="-.",
            label=ANNUAL_INSTALLMENT_LABEL if idx == 0 else "_nolegend_",
        )

    _annotate_vertical_callouts(
        ax,
        _distribution_callouts(
            var95_k=var95_k,
            expected_k=expected_k,
            p95_k=p95_k,
        ),
        y_fracs=(0.78, 0.64, 0.78),
        min_gap_frac=0.09,
        fontsize=7.8,
        text_va="top",
    )

    ax.set_title(
        f"{label}\n{d.get('name', label)}",
        fontsize=12,
        fontweight="bold",
        pad=2,
    )
    ax.set_xlabel(f"Annual value ({unit})")
    if idx == 0:
        ax.set_ylabel("Scenarios")
    _apply_axis_style(ax, grid_axis="y")


def plot_feature_distributions(
    features: dict[str, dict[str, Any]],
    *,
    title: str = "Per-feature business value distribution",
    unit: str = "EUR k",
    divisor: float = 1_000.0,
    colors: dict[str, str] | None = None,
    installment_by_feature: dict[str, float] | None = None,
) -> Figure:
    """N-panel histogram — one per feature with Expected, VaR 95 %, P95 overlays.

    Parameters
    ----------
    features:
        ``{label: {"scenarios": ndarray, "expected": float,
        "var95": float, "p95": float, "name": str}}``
        Values are in raw units; *divisor* is applied for display.
    title:
        Figure super-title.
    unit:
        Axis unit label (e.g. ``"EUR k"``).
    divisor:
        Divide values by this for display (1000 → thousands).
    colors:
        ``{label: hex_color}`` override per feature.
    installment_by_feature:
        Optional mapping of feature label to annual installment cost for annotation.
    """
    labels = list(features.keys())
    n = len(labels)
    default_colors = _cycle_colors(n)
    feat_colors = colors or {lbl: default_colors[i] for i, lbl in enumerate(labels)}

    fig, axes = plt.subplots(1, n, figsize=(6 * n, 5), sharey=True)
    if n == 1:
        axes = [axes]
    fig.suptitle(title, fontsize=16, fontweight="bold", y=0.995)

    for idx, label in enumerate(labels):
        ax = axes[idx]
        d = features[label]
        color = feat_colors[label]
        _draw_feature_distribution_panel(
            ax, idx, label, d, color, divisor, unit, installment_by_feature
        )

    plt.tight_layout(pad=2.0, rect=(0, 0.08, 1, 0.90))
    handles, labels = axes[0].get_legend_handles_labels()
    legend_bottom = _place_bottom_legend(
        fig,
        handles,
        labels,
        max_cols=4,
        fontsize=8.8,
    )
    fig.subplots_adjust(bottom=max(0.20, legend_bottom + 0.01), top=0.86)
    _show_fig(fig)
    return fig


# ── Portfolio Distribution + Stacked Contributions ────────────────────


def plot_portfolio_distribution(
    portfolio_scenarios: np.ndarray,
    feature_contributions: dict[str, float],
    *,
    title: str = "Combined Portfolio \u2014 Risk Profile",
    unit: str = "EUR k",
    divisor: float = 1_000.0,
    colors: dict[str, str] | None = None,
    annual_installment: float | None = None,
    cvar_95: float | None = None,
) -> Figure:
    """Portfolio histogram (left) + stacked contribution bar (right).

    Parameters
    ----------
    portfolio_scenarios:
        1-D array of summed scenario outcomes.
    feature_contributions:
        ``{label: expected_value}`` for each feature.
    title:
        Chart title.
    unit:
        Axis unit label (e.g. ``"EUR k"``).
    divisor:
        Divide values by this for display (1000 → thousands).
    colors:
        Optional mapping of feature label to hex colour string.
    annual_installment:
        Optional total annual installment to annotate on the chart.
    cvar_95:
        Optional CVaR 95% value to annotate on the chart.
    """
    labels = list(feature_contributions.keys())
    default_colors = _cycle_colors(len(labels))
    feat_colors = colors or {lbl: default_colors[i] for i, lbl in enumerate(labels)}

    p_expected = np.mean(portfolio_scenarios)
    p_var95 = float(np.percentile(portfolio_scenarios, 5))

    fig, (ax_dist, ax_stack) = plt.subplots(
        1,
        2,
        figsize=FIG.medium,
        gridspec_kw={"width_ratios": [3, 2]},
    )
    fig.suptitle(title, fontsize=16, fontweight="bold", y=0.995)

    data_k = portfolio_scenarios / divisor

    ax_dist.hist(
        data_k,
        bins=HIST_BINS + 10,
        color=palette["primary"],
        alpha=HIST_ALPHA,
        edgecolor=HIST_EDGE_COLOR,
        linewidth=HIST_EDGE_WIDTH,
        label="Portfolio scenarios",
    )
    ax_dist.axvspan(
        data_k.min(),
        p_var95 / divisor,
        alpha=0.12,
        color=palette["danger"],
        zorder=0,
        lw=0,
        label=DOWNSIDE_ZONE_LABEL,
    )
    ax_dist.axvline(
        p_expected / divisor,
        color=palette["neutral"],
        linewidth=1.8,
        zorder=5,
        label=f"Expected (\u20ac{p_expected / divisor:.0f}k)",
    )
    ax_dist.axvline(
        p_var95 / divisor,
        color=palette["danger"],
        linewidth=1.8,
        linestyle="--",
        zorder=5,
        label=f"VaR 95% (\u20ac{p_var95 / divisor:.0f}k)",
    )
    if cvar_95 is not None:
        p_cvar95 = float(cvar_95)
        ax_dist.axvline(
            p_cvar95 / divisor,
            color=palette["danger"],
            linewidth=1.4,
            linestyle=":",
            zorder=5,
            label=f"CVaR 95% (\u20ac{p_cvar95 / divisor:.0f}k)",
        )
    if annual_installment is not None and annual_installment > 0:
        dep_k = annual_installment / divisor
        ax_dist.axvline(
            dep_k,
            color=palette["danger"],
            linewidth=1.6,
            linestyle="-.",
            zorder=5,
            label=f"Annual Installment (\u20ac{dep_k:.0f}k)",
        )
    y_min, y_max = ax_dist.get_ylim()
    y_span = max(y_max - y_min, 1e-9)
    side_callouts = [
        (
            p_var95 / divisor,
            "VaR 95% Floor",
            palette["danger"],
            -44,
            0.82,
        ),
        (
            p_expected / divisor,
            "Mean (Expected)",
            palette["neutral"],
            44,
            0.68,
        ),
    ]
    if cvar_95 is not None:
        side_callouts.append(
            (float(cvar_95) / divisor, "CVaR 95% Tail", palette["danger"], -44, 0.58)
        )
    for x_val, text, color, x_offset, y_frac in side_callouts:
        y_anchor = y_min + y_span * y_frac
        ax_dist.annotate(
            text,
            xy=(x_val, y_anchor),
            xycoords="data",
            xytext=(x_offset, 0),
            textcoords="offset points",
            ha="right" if x_offset < 0 else "left",
            va="center",
            fontsize=9.4,
            color=color,
            fontweight="bold",
            zorder=8,
            annotation_clip=False,
            bbox={
                "boxstyle": "round,pad=0.28",
                "facecolor": palette["background"],
                "edgecolor": color,
                "linewidth": 1.0,
                "alpha": 0.98,
            },
            arrowprops={
                "arrowstyle": "-",
                "color": color,
                "lw": 1.2,
                "shrinkA": 6,
                "shrinkB": 4,
                "connectionstyle": "arc3,rad=0.0",
            },
        )

    ax_dist.set_title("Portfolio Distribution", fontsize=12, fontweight="bold", pad=6)
    ax_dist.set_xlabel(f"Portfolio Value ({unit}/year)", fontsize=10, labelpad=12)
    ax_dist.set_ylabel("Scenarios", fontsize=10, labelpad=8)
    _apply_axis_style(ax_dist, grid_axis="y")

    # ── Right: stacked contributions ─────────────────────────────────
    bottom = 0.0
    for label in labels:
        val = feature_contributions[label] / divisor
        ax_stack.bar(
            "Expected",
            val,
            bottom=bottom,
            color=feat_colors[label],
            label=label,
            edgecolor=HIST_EDGE_COLOR,
            linewidth=0.5,
        )
        bottom += val

    ax_stack.set_ylabel(f"Value ({unit}/year)", fontsize=10, labelpad=8)
    ax_stack.set_title("Feature Contributions", fontsize=12, fontweight="bold", pad=15)
    _apply_axis_style(ax_stack, grid_axis="y")

    # ── Layout: combined legend centered below both panels ───────────
    plt.tight_layout(pad=2.0, w_pad=2.4, rect=(0, 0.08, 1, 0.90))
    h1, l1 = ax_dist.get_legend_handles_labels()
    h2, l2 = ax_stack.get_legend_handles_labels()
    legend_bottom = _place_bottom_legend(
        fig,
        h1 + h2,
        l1 + l2,
        max_cols=4,
        fontsize=8.5,
    )
    fig.subplots_adjust(bottom=max(0.30, legend_bottom + 0.04), top=0.86)
    _show_fig(fig)
    return fig


# ── Monte Carlo vs. Point Estimate Comparison ────────────────────────


def plot_monte_carlo_comparison(
    result: SimulationResult,
    *,
    development_cost: float,
    business_value_per_conversion: float = 1.0,
    title: str = "A single number hides the risk — the distribution reveals it",
) -> Figure:
    """Two-panel chart comparing a single point estimate with the full MC distribution.

    Left panel shows the expected value as a single bar (traditional business case).
    Right panel shows the histogram of all scenarios with the loss zone shaded.

    Parameters
    ----------
    result:
        A fully computed ``SimulationResult``.
    development_cost:
        Investment threshold used to shade the loss zone.
    business_value_per_conversion:
        Scaling factor applied to raw conversion counts.
    title:
        Overall figure title.
    """
    scenarios = result.results_array
    bv_scenarios = scenarios * business_value_per_conversion
    bv_expected = result.expected_value * business_value_per_conversion

    loss_pct = 100 * float((bv_scenarios < development_cost).mean())

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [1, 2.5]}
    )

    # ── Left: single point estimate ──────────────────────────────────
    ax1.barh(
        ["Single\nestimate"],
        [bv_expected],
        color=palette["primary"],
        height=1.2,
        zorder=3,
    )
    ax1_xlim = max(bv_expected, development_cost) * 1.55
    ax1_left = -ax1_xlim * 0.04  # gap between y-axis and bar start
    ax1.axvline(development_cost, color=palette["danger"], ls="--", lw=1.5, zorder=4)
    ax1.text(
        development_cost,
        0.65,
        f"  Dev cost\n  EUR {development_cost:,.0f}",
        color=palette["danger"],
        fontsize=9,
        va="bottom",
    )
    # Value label inside the bar
    ax1.text(
        bv_expected / 2,
        0,
        f"€{bv_expected:,.0f}",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color=palette["background"],
        zorder=5,
    )
    ax1.set_xlim(ax1_left, ax1_xlim)
    ax1.set_ylim(-0.65, 0.80)
    ax1.set_title("Traditional Business Case", fontsize=10, fontweight="bold")
    ax1.set_xlabel(BUSINESS_VALUE_EUR_LABEL)
    ax1.tick_params(axis="y", length=0)
    _apply_axis_style(ax1, grid_axis="x")

    # ── Right: full Monte Carlo distribution ─────────────────────────
    ax2.hist(
        bv_scenarios,
        bins=HIST_BINS,
        color=palette["primary"],
        alpha=HIST_ALPHA,
        edgecolor=HIST_EDGE_COLOR,
        linewidth=HIST_EDGE_WIDTH,
        zorder=3,
    )
    ax2.axvline(
        bv_expected,
        color=palette["primary"],
        ls="-",
        lw=2,
        label=f"Expected EUR {bv_expected:,.0f}",
        zorder=4,
    )
    ax2.axvline(
        development_cost,
        color=palette["danger"],
        ls="--",
        lw=2,
        label=f"Dev cost EUR {development_cost:,.0f}",
        zorder=4,
    )
    xlim = ax2.get_xlim()
    ax2.axvspan(
        xlim[0], development_cost, alpha=0.12, color=palette["danger"], zorder=2
    )
    center_x = (xlim[0] + development_cost) / 2
    ax2.text(
        center_x,
        ax2.get_ylim()[1] * 0.82,
        f"{loss_pct:.0f}%\nbelow\ncost",
        ha="center",
        fontsize=9,
        fontweight="bold",
        color=palette["danger"],
    )
    ax2.set_title(
        f"Monte Carlo — {len(scenarios):,} Scenarios", fontsize=10, fontweight="bold"
    )
    ax2.set_xlabel(BUSINESS_VALUE_EUR_LABEL)
    ax2.set_ylabel("Frequency")
    ax2.legend(fontsize=8, loc="upper right")
    _apply_axis_style(ax2, grid_axis="y")

    fig.suptitle(title, fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout(pad=1.5)
    _show_fig(fig)
    return fig
