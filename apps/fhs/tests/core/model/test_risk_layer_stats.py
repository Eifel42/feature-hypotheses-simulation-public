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

"""Tests for risk layer value objects."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from fhs.core.model.value_objects import (
    DeliveryStressResult,
    FeatureRiskProfile,
    PortfolioPnLLayers,
    PortfolioRiskLayers,
    PortfolioRiskMeta,
    RetentionMatrix,
    RetentionRow,
    RiskHitRates,
    RiskLayerStats,
    RiskManagementROI,
    RiskProbabilities,
)


def _stats(expected: float) -> RiskLayerStats:
    return RiskLayerStats(
        expected=expected,
        var_95=expected * 0.8,
        cvar_95=expected * 0.7,
        std=expected * 0.1,
    )


def _meta() -> PortfolioRiskMeta:
    return PortfolioRiskMeta(
        market_hit_pct=0.2,
        global_hit_pct=0.05,
        cluster_hit_pct={"Cluster A": 0.1},
        selected=("Feature A", "Feature B"),
        risk_2_probability=0.2,
        risk_3_probability=0.05,
    )


def test_risk_layer_stats_is_immutable() -> None:
    stats = RiskLayerStats(expected=100.0, var_95=80.0, cvar_95=70.0, std=15.0)
    with pytest.raises(FrozenInstanceError):
        stats.expected = 200.0


def test_risk_layer_stats_from_scenarios() -> None:
    scenarios = np.array([100.0, 120.0, 140.0, 160.0, 180.0], dtype=float)

    stats = RiskLayerStats.from_scenarios(scenarios)

    expected_var = float(np.percentile(scenarios, 5))
    tail = scenarios[scenarios <= expected_var]
    expected_cvar = float(np.mean(tail)) if len(tail) > 0 else expected_var

    assert stats.expected == pytest.approx(float(np.mean(scenarios)))
    assert stats.var_95 == pytest.approx(expected_var)
    assert stats.cvar_95 == pytest.approx(expected_cvar)
    assert stats.std == pytest.approx(float(np.std(scenarios)))


def test_feature_risk_profile_construction() -> None:
    profile = FeatureRiskProfile(
        feature="Feature A",
        cluster="Cluster A",
        probabilities=RiskProbabilities(
            risk_1=0.2,
            risk_2=0.2,
            risk_3=0.05,
            component=0.1,
        ),
        base=_stats(1000.0),
        after_risk_1=_stats(900.0),
        after_risk_2=_stats(800.0),
        after_component=_stats(760.0),
        after_risk_3=_stats(700.0),
        hit_rates=RiskHitRates(
            risk_1_blocked_pct=0.2,
            risk_2_hit_pct=0.2,
            component_hit_pct=0.1,
            risk_3_hit_pct=0.05,
        ),
    )
    assert profile.feature == "Feature A"
    assert profile.after_risk_3.expected == 700.0
    assert profile.probabilities.component == 0.1


def test_portfolio_risk_layers_construction() -> None:
    layers = PortfolioRiskLayers(
        base=_stats(2000.0),
        after_risk_1=_stats(1700.0),
        after_risk_2=_stats(1500.0),
        after_component=_stats(1400.0),
        after_risk_3=_stats(1200.0),
        meta=_meta(),
    )
    assert layers.base.expected == 2000.0
    assert layers.after_risk_3.var_95 > 0
    assert layers.meta.selected == ("Feature A", "Feature B")


def test_portfolio_risk_layers_waterfall_summary() -> None:
    layers = PortfolioRiskLayers(
        base=RiskLayerStats(expected=2000.0, var_95=1600.0, cvar_95=1400.0, std=200.0),
        after_risk_1=RiskLayerStats(
            expected=1700.0, var_95=1360.0, cvar_95=1190.0, std=170.0
        ),
        after_risk_2=RiskLayerStats(
            expected=1500.0, var_95=1200.0, cvar_95=1050.0, std=150.0
        ),
        after_component=RiskLayerStats(
            expected=1400.0, var_95=1120.0, cvar_95=980.0, std=140.0
        ),
        after_risk_3=RiskLayerStats(
            expected=1200.0, var_95=960.0, cvar_95=840.0, std=120.0
        ),
        meta=_meta(),
    )

    summary = layers.waterfall_summary()
    assert len(summary.rows) == 5
    assert summary.rows[0].layer_loss == 0.0
    assert summary.rows[-1].layer == "After Global (all risks)"
    assert summary.total_expected_loss == pytest.approx(800.0)
    assert summary.total_expected_loss_pct == pytest.approx(0.4)


def test_portfolio_pnl_layers_construction() -> None:
    layers = PortfolioPnLLayers(
        base=_stats(300.0),
        after_risk_1=_stats(100.0),
        after_risk_2=_stats(0.0),
        after_component=_stats(-20.0),
        after_risk_3=_stats(-120.0),
        meta=_meta(),
    )
    assert layers.after_component.expected == -20.0
    assert layers.after_risk_3.cvar_95 >= layers.after_risk_3.var_95


def test_retention_matrix_construction() -> None:
    matrix = RetentionMatrix(
        rows=(
            RetentionRow(
                feature="Feature A",
                cluster="Cluster A",
                base_expected=1000.0,
                after_risk_3_expected=760.0,
                expected_retention_pct=0.76,
                base_var_95=800.0,
                after_risk_3_var_95=560.0,
                floor_retention_pct=0.70,
            ),
        ),
        portfolio_expected_retention_pct=0.76,
        portfolio_floor_retention_pct=0.70,
    )

    assert matrix.rows[0].feature == "Feature A"
    assert matrix.portfolio_expected_retention_pct == pytest.approx(0.76)


def test_delivery_stress_result_is_immutable() -> None:
    result = DeliveryStressResult(
        prob_success=0.75,
        prob_failure=0.18,
        expected_delay_weeks=4.2,
        expected_impact_eur=125_000.0,
        impact_var_95_eur=210_000.0,
        impact_cvar_95_eur=240_000.0,
    )
    with pytest.raises(FrozenInstanceError):
        result.prob_success = 0.80


def test_risk_management_roi_construction() -> None:
    roi = RiskManagementROI(
        program_cost_eur=7_500.0,
        avoided_expected_loss_eur=18_000.0,
        net_expected_benefit_eur=10_500.0,
        tail_risk_reduction_var_95_eur=26_000.0,
    )
    assert roi.net_expected_benefit_eur > 0
    assert roi.tail_risk_reduction_var_95_eur == 26_000.0
