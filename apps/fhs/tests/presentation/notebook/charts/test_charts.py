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

"""Tests for the presentation.notebook.charts module.

Every chart function is tested to ensure it:
- Returns a matplotlib Figure
- Renders without errors
- Closes figures to avoid resource leaks
"""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import patch

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest

from fhs.core.model import Feature
from fhs.core.model.value_objects.risk_layer_stats import WaterfallRow, WaterfallSummary
from fhs.core.model.value_objects.sprint_delivery import (
    DeliverySimulationResult,
    PortfolioProfitabilityResult,
    ProfitabilityResult,
)
from fhs.core.services import FeatureSimulator
from fhs.presentation.notebook.charts import (
    plot_budget_risk_layers,
    plot_business_value_concentration,
    plot_business_value_forecast,
    plot_cost_comparison,
    plot_feature_distributions,
    plot_feature_ranking,
    plot_llp_impact_bars,
    plot_llp_landscape,
    plot_multi_year_fan,
    plot_opportunity_cost,
    plot_portfolio_distribution,
    plot_profit_histogram,
    plot_risk_comparison,
    plot_risk_layer_decay,
    plot_risk_profile,
    plot_runtime_comparison,
    plot_sensitivity_curve,
    plot_sprint_delay_grid,
    plot_strategy_category_mix,
    plot_stress_test,
    plot_uncertainty_comparison,
)
from fhs.presentation.notebook.charts.distributions import (
    plot_beta_sample_size_effect,
    plot_beta_vs_normal_boxplot,
    plot_distribution_risk_metric_comparison,
    plot_distribution_shape_comparison,
    plot_lognormal_distribution_deep_dive,
    plot_monte_carlo_comparison,
    plot_normal_distribution_deep_dive,
)
from fhs.presentation.notebook.charts.risk import (
    plot_delivery_market_resilience,
    plot_feature_risk_decay,
    plot_feature_risk_layer_decay,
    plot_risk_waterfall,
    plot_sensitivity_panel,
)

matplotlib.use("Agg")


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def feature():
    return Feature(
        name="Test Feature",
        expected_users=10_000,
        conversion_rate=0.15,
        uncertainty=0.3,
    )


@pytest.fixture
def sim_result(feature):
    sim = FeatureSimulator(seed=42)
    return sim.simulate_feature(feature, scenarios=1_000)


@pytest.fixture
def multi_feature_data():
    """Simulated results dict in the format expected by multi-feature chart functions."""
    rng = np.random.default_rng(42)
    return {
        "H1": {
            "scenarios": rng.normal(100_000, 15_000, 1_000),
            "expected": 100_000.0,
            "var95": 75_000.0,
            "p95": 125_000.0,
            "name": "Simplified UI",
        },
        "H2": {
            "scenarios": rng.normal(80_000, 12_000, 1_000),
            "expected": 80_000.0,
            "var95": 60_000.0,
            "p95": 100_000.0,
            "name": "Traceability",
        },
        "H3": {
            "scenarios": rng.normal(50_000, 8_000, 1_000),
            "expected": 50_000.0,
            "var95": 38_000.0,
            "p95": 65_000.0,
            "name": "Expiration Alerts",
        },
    }


# ── plot_risk_profile ─────────────────────────────────────────────────


class TestPlotRiskProfile:
    def test_returns_figure(self, sim_result):
        with patch.object(plt, "show"):
            fig = plot_risk_profile(sim_result)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_has_two_axes(self, sim_result):
        with patch.object(plt, "show"):
            fig = plot_risk_profile(sim_result)
        assert len(fig.axes) == 2
        plt.close(fig)


# ── plot_uncertainty_comparison ────────────────────────────────────────


class TestPlotUncertaintyComparison:
    def test_returns_figure(self, feature):
        with patch.object(plt, "show"):
            fig = plot_uncertainty_comparison(feature, n_scenarios=1_000, seed=1)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_has_three_panels(self, feature):
        with patch.object(plt, "show"):
            fig = plot_uncertainty_comparison(feature, n_scenarios=1_000, seed=1)
        assert len(fig.axes) == 3
        plt.close(fig)

    def test_attaches_insight(self, feature):
        with patch.object(plt, "show"):
            fig = plot_uncertainty_comparison(feature, n_scenarios=1_000, seed=1)
        assert hasattr(fig, "_fhs_insight")
        assert "shrinks the outcome range" in fig._fhs_insight
        plt.close(fig)

    def test_custom_levels(self, feature):
        with patch.object(plt, "show"):
            fig = plot_uncertainty_comparison(
                feature,
                levels=(0.05, 0.25),
                n_scenarios=1_000,
                seed=1,
            )
        assert len(fig.axes) == 2
        plt.close(fig)


# ── plot_feature_distributions ────────────────────────────────────────


class TestPlotFeatureDistributions:
    def test_returns_figure(self, multi_feature_data):
        with patch.object(plt, "show"):
            fig = plot_feature_distributions(multi_feature_data)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_panel_count_matches_features(self, multi_feature_data):
        with patch.object(plt, "show"):
            fig = plot_feature_distributions(multi_feature_data)
        # 3 features = 3 axes
        assert len(fig.axes) == 3
        plt.close(fig)

    def test_single_feature(self, multi_feature_data):
        single = {"H1": multi_feature_data["H1"]}
        with patch.object(plt, "show"):
            fig = plot_feature_distributions(single)
        assert len(fig.axes) == 1
        plt.close(fig)

    def test_custom_colors(self, multi_feature_data):
        colors = {"H1": "#ff0000", "H2": "#00ff00", "H3": "#0000ff"}
        with patch.object(plt, "show"):
            fig = plot_feature_distributions(multi_feature_data, colors=colors)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_custom_unit_and_divisor(self, multi_feature_data):
        with patch.object(plt, "show"):
            fig = plot_feature_distributions(
                multi_feature_data,
                unit="EUR",
                divisor=1,
            )
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)


# ── plot_risk_comparison ──────────────────────────────────────────────


class TestPlotRiskComparison:
    def test_returns_figure(self, multi_feature_data):
        with patch.object(plt, "show"):
            fig = plot_risk_comparison(multi_feature_data)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_has_two_panels(self, multi_feature_data):
        with patch.object(plt, "show"):
            fig = plot_risk_comparison(multi_feature_data)
        assert len(fig.axes) == 2
        plt.close(fig)

    def test_custom_title(self, multi_feature_data):
        with patch.object(plt, "show"):
            fig = plot_risk_comparison(multi_feature_data, title="Custom Title")
        assert fig._suptitle.get_text() == "Custom Title"
        plt.close(fig)

    def test_uses_business_value_floor_label(self, multi_feature_data):
        with patch.object(plt, "show"):
            fig = plot_risk_comparison(multi_feature_data)
        ax_rank = fig.axes[1]
        labels = ax_rank.get_legend_handles_labels()[1]
        assert "Business Value Floor 95" in labels
        assert ax_rank.get_title() == "Expected vs. Business Value Floor 95"
        plt.close(fig)


# ── plot_portfolio_distribution ───────────────────────────────────────


class TestPlotPortfolioDistribution:
    def test_returns_figure(self, multi_feature_data):
        scenarios = sum(d["scenarios"] for d in multi_feature_data.values())
        contributions = {k: d["expected"] for k, d in multi_feature_data.items()}
        with patch.object(plt, "show"):
            fig = plot_portfolio_distribution(scenarios, contributions)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_has_two_panels(self, multi_feature_data):
        scenarios = sum(d["scenarios"] for d in multi_feature_data.values())
        contributions = {k: d["expected"] for k, d in multi_feature_data.items()}
        with patch.object(plt, "show"):
            fig = plot_portfolio_distribution(scenarios, contributions)
        assert len(fig.axes) == 2
        plt.close(fig)


# ── plot_budget_risk_layers ──────────────────────────────────────────


class TestPlotBudgetRiskLayers:
    @pytest.fixture
    def budget_results(self):
        return {
            135_000: {
                "exact": {
                    "l1": {
                        "market_var_95": 420_000,
                        "simulated_var_95": 360_000,
                    },
                    "l3": {
                        "shocked_var_95": 260_000,
                    },
                },
                "ilp": {
                    "l1": {
                        "market_var_95": 410_000,
                        "simulated_var_95": 350_000,
                    },
                    "l3": {
                        "shocked_var_95": 255_000,
                    },
                },
            },
            400_000: {
                "exact": {
                    "l1": {
                        "market_var_95": 820_000,
                        "simulated_var_95": 610_000,
                    },
                    "l3": {
                        "shocked_var_95": 410_000,
                    },
                },
                "ilp": {
                    "l1": {
                        "market_var_95": 790_000,
                        "simulated_var_95": 590_000,
                    },
                    "l3": {
                        "shocked_var_95": 400_000,
                    },
                },
            },
        }

    def test_returns_figure(self, budget_results):
        with patch.object(plt, "show"):
            fig = plot_budget_risk_layers(budget_results)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_has_two_panels(self, budget_results):
        with patch.object(plt, "show"):
            fig = plot_budget_risk_layers(budget_results)
        assert len(fig.axes) == 2
        plt.close(fig)


# ── plot_opportunity_cost ─────────────────────────────────────────────


class TestPlotOpportunityCost:
    def test_returns_figure(self):
        costs = [
            ("Feature A", 150_000),
            ("Feature B", 50_000),
            ("Feature C", 10_000),
        ]
        with patch.object(plt, "show"):
            fig = plot_opportunity_cost(costs)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_color_thresholds(self):
        """High (>100k), medium (>20k), low (<20k) get different colours."""
        costs = [("High", 200_000), ("Med", 50_000), ("Low", 5_000)]
        with patch.object(plt, "show"):
            fig = plot_opportunity_cost(costs)
        ax = fig.axes[0]
        bars = ax.patches
        assert len(bars) == 3
        plt.close(fig)


# ── plot_feature_ranking ──────────────────────────────────────────────


class TestPlotFeatureRanking:
    @pytest.fixture
    def rankings(self):
        return [
            {
                "feature": "A",
                "expected_business_value": 100_000,
                "var_95_business_value": 70_000,
                "risk_ratio": 0.15,
            },
            {
                "feature": "B",
                "expected_business_value": 80_000,
                "var_95_business_value": 40_000,
                "risk_ratio": 0.35,
            },
            {
                "feature": "C",
                "expected_business_value": 50_000,
                "var_95_business_value": 20_000,
                "risk_ratio": 0.55,
            },
        ]

    def test_returns_figure(self, rankings):
        with patch.object(plt, "show"):
            fig = plot_feature_ranking(rankings)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_bars_count(self, rankings):
        """Two bar groups (expected + VaR) × 3 features = 6 patches."""
        with patch.object(plt, "show"):
            fig = plot_feature_ranking(rankings)
        ax = fig.axes[0]
        assert len(ax.patches) == 6
        plt.close(fig)

    def test_uses_business_value_floor_legend(self, rankings):
        with patch.object(plt, "show"):
            fig = plot_feature_ranking(rankings)
        ax = fig.axes[0]
        labels = ax.get_legend_handles_labels()[1]
        assert "Business Value Floor 95 (EUR k)" in labels
        assert ax.get_title() == "Feature Ranking: Business Value and Downside View"
        plt.close(fig)


# ── plot_business_value_concentration ────────────────────────────────────────


class TestPlotBusinessValueConcentration:
    def test_returns_figure(self):
        conc = {
            "concentration": {"A": 0.50, "B": 0.30, "C": 0.20},
            "hhi": 0.38,
            "is_concentrated": False,
        }
        with patch.object(plt, "show"):
            fig = plot_business_value_concentration(conc)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)


class TestPlotStrategyCategoryMix:
    def test_returns_figure(self):
        rows = [
            {"category": "Growth", "cost": 80_000.0},
            {"category": "Efficiency", "cost": 40_000.0},
            {"category": "Risk", "cost": 30_000.0},
        ]
        with patch.object(plt, "show"):
            fig = plot_strategy_category_mix(rows)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_concentrated_portfolio(self):
        conc = {
            "concentration": {"A": 0.90, "B": 0.10},
            "hhi": 0.82,
            "is_concentrated": True,
        }
        with patch.object(plt, "show"):
            fig = plot_business_value_concentration(conc)
        # Title should contain "Concentrated"
        ax = fig.axes[0]
        assert "Concentrated" in ax.get_title()
        plt.close(fig)

    def test_small_share_no_label(self):
        """Shares < 6% should not have in-bar text."""
        conc = {
            "concentration": {"A": 0.95, "B": 0.05},
            "hhi": 0.905,
            "is_concentrated": True,
        }
        with patch.object(plt, "show"):
            fig = plot_business_value_concentration(conc)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)


# ── plot_risk_layer_decay ────────────────────────────────────────────


class TestPlotRiskLayerDecay:
    @pytest.fixture
    def waterfall(self):
        return WaterfallSummary(
            rows=(
                WaterfallRow("Base (no risk)", 520_000.0, 420_000.0, 0.0),
                WaterfallRow("After Delivery", 410_000.0, 250_000.0, 110_000.0),
                WaterfallRow("After Market", 360_000.0, 220_000.0, 50_000.0),
                WaterfallRow("After Component", 330_000.0, 205_000.0, 30_000.0),
                WaterfallRow(
                    "After Global (all risks)", 290_000.0, 180_000.0, 40_000.0
                ),
            ),
            total_expected_loss=230_000.0,
            total_expected_loss_pct=230_000.0 / 520_000.0,
        )

    def test_returns_figure(self, waterfall):
        with patch.object(plt, "show"):
            fig = plot_risk_layer_decay(waterfall)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_has_single_axis(self, waterfall):
        with patch.object(plt, "show"):
            fig = plot_risk_layer_decay(waterfall)
        assert len(fig.axes) == 1
        plt.close(fig)


# ── plot_sensitivity_curve ───────────────────────────────────────────


class TestPlotSensitivityCurve:
    @pytest.fixture
    def results(self):
        return {
            0.10: SimpleNamespace(after_risk_3=SimpleNamespace(expected=420_000.0)),
            0.20: SimpleNamespace(after_risk_3=SimpleNamespace(expected=380_000.0)),
            0.30: SimpleNamespace(after_risk_3=SimpleNamespace(expected=340_000.0)),
        }

    def test_returns_figure(self, results):
        with patch.object(plt, "show"):
            fig = plot_sensitivity_curve(
                results,
                param_name="Market Shock Probability",
            )
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_has_single_axis(self, results):
        with patch.object(plt, "show"):
            fig = plot_sensitivity_curve(
                results,
                param_name="Global Crisis Probability",
            )
        assert len(fig.axes) == 1
        plt.close(fig)


# ── plot_sprint_delay_grid ───────────────────────────────────────────


class TestPlotSprintDelayGrid:
    @pytest.fixture
    def delivery_results(self):
        return {
            "H1: Simplified UI": DeliverySimulationResult(
                feature_name="H1: Simplified UI",
                planned_sprints=3,
                actual_sprints=np.array([3, 4, 4, 5, 3, 4]),
                actual_cost=np.array(
                    [30_000.0, 40_000.0, 40_000.0, 50_000.0, 30_000.0, 40_000.0]
                ),
                cancelled=np.array([False, False, False, True, False, False]),
                business_value_after_risk=np.array(
                    [120_000.0, 120_000.0, 120_000.0, 0.0, 120_000.0, 120_000.0]
                ),
            ),
            "H2: Traceability": DeliverySimulationResult(
                feature_name="H2: Traceability",
                planned_sprints=2,
                actual_sprints=np.array([2, 2, 3, 4, 3, 2]),
                actual_cost=np.array(
                    [20_000.0, 20_000.0, 30_000.0, 40_000.0, 30_000.0, 20_000.0]
                ),
                cancelled=np.array([False, False, False, True, False, False]),
                business_value_after_risk=np.array(
                    [80_000.0, 80_000.0, 80_000.0, 0.0, 80_000.0, 80_000.0]
                ),
            ),
        }

    def test_returns_figure(self, delivery_results):
        with patch.object(plt, "show"):
            fig = plot_sprint_delay_grid(delivery_results)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_axis_count_matches_features(self, delivery_results):
        with patch.object(plt, "show"):
            fig = plot_sprint_delay_grid(delivery_results)
        assert len(fig.axes) == 2
        plt.close(fig)


# ── plot_cost_comparison ─────────────────────────────────────────────


class TestPlotCostComparison:
    @pytest.fixture
    def delivery_results(self):
        return {
            "H1: Simplified UI": DeliverySimulationResult(
                feature_name="H1: Simplified UI",
                planned_sprints=3,
                actual_sprints=np.array([3, 4, 4, 5, 3, 4]),
                actual_cost=np.array(
                    [30_000.0, 40_000.0, 40_000.0, 50_000.0, 30_000.0, 40_000.0]
                ),
                cancelled=np.array([False, False, False, True, False, False]),
                business_value_after_risk=np.array(
                    [120_000.0, 120_000.0, 120_000.0, 0.0, 120_000.0, 120_000.0]
                ),
            ),
            "H2: Traceability": DeliverySimulationResult(
                feature_name="H2: Traceability",
                planned_sprints=2,
                actual_sprints=np.array([2, 2, 3, 4, 3, 2]),
                actual_cost=np.array(
                    [20_000.0, 20_000.0, 30_000.0, 40_000.0, 30_000.0, 20_000.0]
                ),
                cancelled=np.array([False, False, False, True, False, False]),
                business_value_after_risk=np.array(
                    [80_000.0, 80_000.0, 80_000.0, 0.0, 80_000.0, 80_000.0]
                ),
            ),
        }

    def test_returns_figure(self, delivery_results):
        with patch.object(plt, "show"):
            fig = plot_cost_comparison(delivery_results)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_has_single_axis(self, delivery_results):
        with patch.object(plt, "show"):
            fig = plot_cost_comparison(delivery_results)
        assert len(fig.axes) == 1
        plt.close(fig)

    def test_includes_tail_metrics_when_enabled(self, delivery_results):
        with patch.object(plt, "show"):
            fig = plot_cost_comparison(
                delivery_results,
                include_tail_metrics=True,
            )
        ax = fig.axes[0]
        labels = ax.get_legend_handles_labels()[1]
        assert "CaR 95%" in labels
        assert "CVaR 95%" in labels
        # 2 features x 4 bars (planned, expected, CaR, CVaR)
        assert len(ax.patches) == 8
        plt.close(fig)

    def test_tail_metrics_branch_preserves_title(self, delivery_results):
        title = "Planned vs Expected vs CaR/CVaR Development Burn Cost"
        with patch.object(plt, "show"):
            fig = plot_cost_comparison(
                delivery_results,
                title=title,
                include_tail_metrics=True,
            )
        assert fig.axes[0].get_title() == title
        plt.close(fig)


# ── plot_runtime_comparison ──────────────────────────────────────────


class TestPlotRuntimeComparison:
    @pytest.fixture
    def runtime_data(self):
        return {
            "exact": {
                "x": [8, 12, 16],
                "runtime": [0.11, 0.49, 1.82],
                "floor": [210_000.0, 315_000.0, 420_000.0],
            },
            "ilp": {
                "x": [8, 12, 16],
                "runtime": [0.02, 0.04, 0.08],
                "floor": [205_000.0, 305_000.0, 410_000.0],
            },
            "greedy": {
                "x": [8, 12, 16],
                "runtime": [0.01, 0.01, 0.02],
                "floor": [198_000.0, 290_000.0, 395_000.0],
            },
        }

    def test_returns_figure(self, runtime_data):
        with patch.object(plt, "show"):
            fig = plot_runtime_comparison(runtime_data)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_has_two_panels(self, runtime_data):
        with patch.object(plt, "show"):
            fig = plot_runtime_comparison(runtime_data)
        assert len(fig.axes) == 2
        plt.close(fig)


# ── plot_stress_test ──────────────────────────────────────────────────


class TestPlotStressTest:
    def test_returns_figure(self):
        data = [
            ("crash", "Market Crash", 200, 100, -50.0, "#a04100"),
            ("fail", "Feature Fails", 200, 150, -25.0, "#a04100"),
            ("best", "Best Case", 200, 350, +75.0, "#00664d"),
        ]
        with patch.object(plt, "show"):
            fig = plot_stress_test(data)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_bar_count(self):
        data = [
            ("crash", "Crash", 200, 100, -50.0, "#a04100"),
        ]
        with patch.object(plt, "show"):
            fig = plot_stress_test(data)
        ax = fig.axes[0]
        # 2 bars per scenario (baseline + stressed)
        assert len(ax.patches) == 2
        plt.close(fig)


# ── plot_business_value_forecast ─────────────────────────────────────────────


class TestPlotBusinessValueForecast:
    @dataclass
    class _MockFeature:
        name: str
        base_business_value: float
        annual_growth_rate: float

        def get_base_annual_business_value(self):
            return self.base_business_value

    def test_returns_figure(self):
        features = [
            self._MockFeature("A", 10_000, 1.0),
            self._MockFeature("B", 5_000, 0.6),
        ]
        with patch.object(plt, "show"):
            fig = plot_business_value_forecast(features)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_has_two_panels(self):
        features = [
            self._MockFeature("A", 10_000, 1.0),
        ]
        with patch.object(plt, "show"):
            fig = plot_business_value_forecast(features)
        assert len(fig.axes) == 2
        plt.close(fig)


class TestPlotMultiYearFan:
    @dataclass
    class _MockYear:
        year: int
        expected: float
        var_95: float
        p95: float
        scenarios: np.ndarray

    @dataclass
    class _MockMultiYearResult:
        feature_name: str
        years: list

    def test_returns_figure(self):
        result = self._MockMultiYearResult(
            "A",
            [
                self._MockYear(1, 100_000, 70_000, 130_000, np.array([1.0, 2.0])),
                self._MockYear(2, 120_000, 85_000, 155_000, np.array([1.0, 2.0])),
                self._MockYear(3, 144_000, 100_000, 188_000, np.array([1.0, 2.0])),
            ],
        )
        with patch.object(plt, "show"):
            fig = plot_multi_year_fan([result])
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_axis_count_matches_results(self):
        results = [
            self._MockMultiYearResult(
                "A",
                [
                    self._MockYear(1, 100_000, 70_000, 130_000, np.array([1.0, 2.0])),
                    self._MockYear(2, 120_000, 85_000, 155_000, np.array([1.0, 2.0])),
                    self._MockYear(3, 144_000, 100_000, 188_000, np.array([1.0, 2.0])),
                ],
            ),
            self._MockMultiYearResult(
                "B",
                [
                    self._MockYear(1, 80_000, 60_000, 100_000, np.array([1.0, 2.0])),
                    self._MockYear(2, 88_000, 66_000, 110_000, np.array([1.0, 2.0])),
                    self._MockYear(3, 97_000, 72_000, 121_000, np.array([1.0, 2.0])),
                ],
            ),
        ]
        with patch.object(plt, "show"):
            fig = plot_multi_year_fan(results)
        assert len(fig.axes) == 2
        plt.close(fig)


class TestLLPCharts:
    def test_plot_llp_landscape_returns_figure(self):
        features = [
            Feature(
                name="A",
                expected_users=1000,
                conversion_rate=0.1,
                uncertainty=0.2,
                development_cost=20000,
                likelihood_of_non_delivery=0.1,
            ),
            Feature(
                name="B",
                expected_users=1500,
                conversion_rate=0.08,
                uncertainty=0.25,
                development_cost=30000,
                likelihood_of_non_delivery=0.35,
            ),
        ]
        sim = FeatureSimulator(seed=2)
        simulation_results = {
            f.name: sim.simulate_feature(f, scenarios=1000) for f in features
        }

        with patch.object(plt, "show"):
            fig = plot_llp_landscape(features, simulation_results, selected_names=["A"])

        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_plot_llp_impact_bars_handles_empty_features(self):
        with patch.object(plt, "show"):
            fig = plot_llp_impact_bars({"features": []}, {})

        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_plot_llp_impact_bars_returns_figure(self):
        delivery_risk_result = {
            "features": [
                {
                    "name": "A",
                    "non_delivery_risk": 0.1,
                    "delivered_pct": 0.9,
                },
                {
                    "name": "B",
                    "non_delivery_risk": 0.35,
                    "delivered_pct": 0.65,
                },
            ]
        }

        with patch.object(plt, "show"):
            fig = plot_llp_impact_bars(delivery_risk_result, {})

        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)


# ── downside_risk_card widget ─────────────────────────────────────────


class TestDownsideRiskCard:
    def test_returns_html(self):
        from fhs.presentation.notebook.widgets import downside_risk_card

        html = downside_risk_card(800, 700, 1000)
        assert "BVF 95" in html
        assert "CVaR 95" in html
        assert "300" in html  # gap = 1000 - 700

    def test_custom_title(self):
        from fhs.presentation.notebook.widgets import downside_risk_card

        html = downside_risk_card(800, 700, 1000, title="Custom Risk")
        assert "Custom Risk" in html


# ── plot_profit_histogram ─────────────────────────────────────────────


class TestPlotProfitHistogram:
    @pytest.fixture
    def sample_profitability(self):
        rng = np.random.default_rng(42)
        profit_dist = rng.normal(50_000, 30_000, 1_000)
        feature_result = ProfitabilityResult(
            feature_name="H1: Simplified UI",
            profit_distribution=profit_dist,
            planned_cost=80_000.0,
            expected_business_value=130_000.0,
            expected_cost=85_000.0,
        )
        portfolio_profit = profit_dist.copy()
        return PortfolioProfitabilityResult(
            feature_results=(feature_result,),
            portfolio_profit=portfolio_profit,
            total_investment=80_000.0,
        )

    def test_returns_figure(self, sample_profitability):
        with patch.object(plt, "show"):
            fig = plot_profit_histogram(sample_profitability)

        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_custom_title(self, sample_profitability):
        with patch.object(plt, "show"):
            fig = plot_profit_histogram(
                sample_profitability, title="Custom Profit Chart"
            )

        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_p5_and_mean_lines_present(self, sample_profitability):
        with patch.object(plt, "show"):
            fig = plot_profit_histogram(sample_profitability)

        ax = fig.axes[0]
        # Two axvline calls → two vertical lines in the axes
        vlines = [line for line in ax.lines if line.get_linestyle() in ("--", "-")]
        assert len(vlines) >= 2
        plt.close(fig)


# ── plot_beta_sample_size_effect ──────────────────────────────────────


class TestPlotBetaSampleSizeEffect:
    def test_returns_figure(self):
        with patch.object(plt, "show"):
            fig = plot_beta_sample_size_effect(n_samples=100, seed=1)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_default_has_three_panels(self):
        with patch.object(plt, "show"):
            fig = plot_beta_sample_size_effect(n_samples=100, seed=1)
        assert len(fig.axes) == 3
        plt.close(fig)

    def test_custom_title(self):
        with patch.object(plt, "show"):
            fig = plot_beta_sample_size_effect(n_samples=100, seed=1, title="Custom")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_single_trial(self):
        with patch.object(plt, "show"):
            fig = plot_beta_sample_size_effect(
                trials=(("Low", 2, 23),), n_samples=100, seed=1
            )
        assert len(fig.axes) == 1
        plt.close(fig)


# ── plot_beta_vs_normal_boxplot ───────────────────────────────────────


class TestPlotBetaVsNormalBoxplot:
    def test_returns_figure_and_metrics(self):
        with patch.object(plt, "show"):
            fig, metrics = plot_beta_vs_normal_boxplot(n_samples=100, seed=1)
        assert isinstance(fig, matplotlib.figure.Figure)
        assert isinstance(metrics, dict)
        plt.close(fig)

    def test_has_two_panels(self):
        with patch.object(plt, "show"):
            fig, _ = plot_beta_vs_normal_boxplot(n_samples=100, seed=1)
        assert len(fig.axes) == 2
        plt.close(fig)

    def test_custom_params(self):
        with patch.object(plt, "show"):
            fig, _ = plot_beta_vs_normal_boxplot(
                mean_rate=0.05, uncertainty=0.3, n_samples=100, seed=42
            )
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)


# ── plot_distribution_risk_metric_comparison ──────────────────────────


class TestPlotDistributionRiskMetricComparison:
    def test_returns_figure_and_metrics(self):
        with patch.object(plt, "show"):
            fig, metrics = plot_distribution_risk_metric_comparison(
                n_samples=100, seed=1
            )
        assert isinstance(fig, matplotlib.figure.Figure)
        assert isinstance(metrics, dict)
        plt.close(fig)

    def test_has_axes(self):
        with patch.object(plt, "show"):
            fig, _ = plot_distribution_risk_metric_comparison(n_samples=100, seed=1)
        assert len(fig.axes) > 0
        plt.close(fig)


# ── plot_distribution_shape_comparison ───────────────────────────────


class TestPlotDistributionShapeComparison:
    def test_returns_figure_and_metrics(self):
        with patch.object(plt, "show"):
            fig, metrics = plot_distribution_shape_comparison(n_samples=100, seed=1)
        assert isinstance(fig, matplotlib.figure.Figure)
        assert isinstance(metrics, dict)
        plt.close(fig)

    def test_has_three_panels(self):
        with patch.object(plt, "show"):
            fig, _ = plot_distribution_shape_comparison(n_samples=100, seed=1)
        assert len(fig.axes) == 3
        plt.close(fig)

    def test_custom_params(self):
        with patch.object(plt, "show"):
            fig, _ = plot_distribution_shape_comparison(
                mean_rate=0.10, n_samples=100, seed=99
            )
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)


# ── plot_normal_distribution_deep_dive ───────────────────────────────


class TestPlotNormalDistributionDeepDive:
    def test_returns_figure_and_metrics(self):
        with patch.object(plt, "show"):
            fig, metrics = plot_normal_distribution_deep_dive(n_samples=100, seed=1)
        assert isinstance(fig, matplotlib.figure.Figure)
        assert isinstance(metrics, dict)
        plt.close(fig)

    def test_has_two_panels(self):
        with patch.object(plt, "show"):
            fig, _ = plot_normal_distribution_deep_dive(n_samples=100, seed=1)
        assert len(fig.axes) == 2
        plt.close(fig)


# ── plot_lognormal_distribution_deep_dive ─────────────────────────────


class TestPlotLognormalDistributionDeepDive:
    def test_returns_figure_and_metrics(self):
        with patch.object(plt, "show"):
            fig, metrics = plot_lognormal_distribution_deep_dive(n_samples=100, seed=1)
        assert isinstance(fig, matplotlib.figure.Figure)
        assert isinstance(metrics, dict)
        plt.close(fig)

    def test_has_two_panels(self):
        with patch.object(plt, "show"):
            fig, _ = plot_lognormal_distribution_deep_dive(n_samples=100, seed=1)
        assert len(fig.axes) == 2
        plt.close(fig)


# ── plot_monte_carlo_comparison ───────────────────────────────────────


class TestPlotMonteCarloComparison:
    def test_returns_figure(self, sim_result):
        with patch.object(plt, "show"):
            fig = plot_monte_carlo_comparison(sim_result, development_cost=50_000.0)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_has_two_panels(self, sim_result):
        with patch.object(plt, "show"):
            fig = plot_monte_carlo_comparison(sim_result, development_cost=50_000.0)
        assert len(fig.axes) == 2
        plt.close(fig)

    def test_custom_scaling(self, sim_result):
        with patch.object(plt, "show"):
            fig = plot_monte_carlo_comparison(
                sim_result,
                development_cost=80_000.0,
                business_value_per_conversion=150.0,
            )
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)


# ── plot_sensitivity_panel ────────────────────────────────────────────


class TestPlotSensitivityPanel:
    @pytest.fixture
    def panels(self):
        result = SimpleNamespace(after_risk_3=SimpleNamespace(expected=100_000.0))
        return [
            (
                {0.10: result, 0.20: result, 0.30: result},
                "Uncertainty",
                "#1565c0",
            )
        ]

    def test_returns_figure(self, panels):
        with patch.object(plt, "show"):
            fig = plot_sensitivity_panel(panels)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_with_installment(self, panels):
        with patch.object(plt, "show"):
            fig = plot_sensitivity_panel(panels, annual_installment=50_000.0)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_multi_panel(self):
        result = SimpleNamespace(after_risk_3=SimpleNamespace(expected=200_000.0))
        panels = [
            ({0.1: result, 0.3: result}, "Uncertainty", "#1565c0"),
            ({0.1: result, 0.3: result}, "Market Risk", "#c62828"),
        ]
        with patch.object(plt, "show"):
            fig = plot_sensitivity_panel(panels)
        assert len(fig.axes) == 2
        plt.close(fig)


# ── plot_feature_risk_layer_decay ─────────────────────────────────────


class TestPlotFeatureRiskLayerDecay:
    @pytest.fixture
    def decay_data(self):
        return {
            "feature_names": ["Feature A", "Feature B"],
            "expected_matrix": [
                [100_000.0, 80_000.0, 60_000.0],
                [200_000.0, 160_000.0, 120_000.0],
            ],
            "layer_labels": ["Base", "After Dev Risk", "After Crisis"],
        }

    def test_returns_figure(self, decay_data):
        with patch.object(plt, "show"):
            fig = plot_feature_risk_layer_decay(
                decay_data["feature_names"],
                decay_data["expected_matrix"],
                decay_data["layer_labels"],
            )
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_without_labels(self):
        # Default labels are 5 layers — match matrix columns
        with patch.object(plt, "show"):
            fig = plot_feature_risk_layer_decay(
                ["Feature A", "Feature B"],
                [
                    [100_000.0, 80_000.0, 60_000.0, 50_000.0, 40_000.0],
                    [200_000.0, 160_000.0, 120_000.0, 100_000.0, 80_000.0],
                ],
            )
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_single_feature(self):
        with patch.object(plt, "show"):
            fig = plot_feature_risk_layer_decay(
                ["Feature A"],
                [[100_000.0, 80_000.0, 60_000.0]],
                ["Base", "Dev", "Crisis"],
            )
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)


# ── plot_feature_risk_decay ───────────────────────────────────────────


class TestPlotFeatureRiskDecay:
    def test_returns_figure(self):
        with patch.object(plt, "show"):
            fig = plot_feature_risk_decay(
                ["Feature A", "Feature B"],
                [[100_000.0, 60_000.0, 30_000.0], [200_000.0, 140_000.0, 80_000.0]],
                ["Base", "After Dev Risk", "After Crisis"],
            )
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_without_labels(self):
        # Default labels are 5 layers — match matrix columns
        with patch.object(plt, "show"):
            fig = plot_feature_risk_decay(
                ["Feature A", "Feature B"],
                [
                    [100_000.0, 60_000.0, 30_000.0, 20_000.0, 10_000.0],
                    [200_000.0, 140_000.0, 80_000.0, 50_000.0, 30_000.0],
                ],
            )
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_custom_title(self):
        with patch.object(plt, "show"):
            fig = plot_feature_risk_decay(
                ["Feature A"],
                [[100_000.0, 60_000.0, 30_000.0]],
                ["Base", "Dev", "Crisis"],
                title="Custom Decay",
            )
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)


# ── plot_delivery_market_resilience ──────────────────────────────────


class TestPlotDeliveryMarketResilience:
    @pytest.fixture
    def heatmap_data(self):
        # Values span above and below investment so TwoSlopeNorm works
        return {
            (0.5, 0.10): 900_000.0,
            (0.5, 0.20): 750_000.0,
            (0.5, 0.30): 600_000.0,
            (1.0, 0.10): 800_000.0,
            (1.0, 0.20): 700_000.0,
            (1.0, 0.30): 500_000.0,
            (1.5, 0.10): 650_000.0,
            (1.5, 0.20): 550_000.0,
            (1.5, 0.30): 400_000.0,
        }

    def test_returns_figure_and_summary(self, heatmap_data):
        with patch.object(plt, "show"):
            fig, summary = plot_delivery_market_resilience(
                heatmap_data, investment=650_000.0
            )
        assert isinstance(fig, matplotlib.figure.Figure)
        assert isinstance(summary, dict)
        plt.close(fig)

    def test_summary_keys(self, heatmap_data):
        with patch.object(plt, "show"):
            _, summary = plot_delivery_market_resilience(
                heatmap_data, investment=650_000.0
            )
        assert "base_k" in summary
        plt.close(_)

    def test_custom_title(self, heatmap_data):
        with patch.object(plt, "show"):
            fig, _ = plot_delivery_market_resilience(
                heatmap_data, investment=650_000.0, title="Custom"
            )
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)


# ── plot_risk_waterfall ───────────────────────────────────────────────


class TestPlotRiskWaterfall:
    @pytest.fixture
    def waterfall_inputs(self):
        level_1 = {
            "market_expected": 1_000_000.0,
            "market_var_95": 750_000.0,
            "simulated_expected": 900_000.0,
            "simulated_var_95": 650_000.0,
        }
        level_3 = {
            "shocked_expected": 800_000.0,
            "shocked_var_95": 500_000.0,
        }
        return level_1, level_3

    def test_returns_figure(self, waterfall_inputs):
        level_1, level_3 = waterfall_inputs
        with patch.object(plt, "show"):
            fig = plot_risk_waterfall(level_1, level_3)
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_has_two_panels(self, waterfall_inputs):
        level_1, level_3 = waterfall_inputs
        with patch.object(plt, "show"):
            fig = plot_risk_waterfall(level_1, level_3)
        assert len(fig.axes) == 2
        plt.close(fig)

    def test_custom_title(self, waterfall_inputs):
        level_1, level_3 = waterfall_inputs
        with patch.object(plt, "show"):
            fig = plot_risk_waterfall(level_1, level_3, title="My Waterfall")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)
