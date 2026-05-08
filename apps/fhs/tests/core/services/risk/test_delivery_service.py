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

"""Tests for DeliveryRiskService."""

from __future__ import annotations

import numpy as np

from fhs.core.model import (
    DeliveryStressResult,
    Feature,
    PnLAssessment,
    PortfolioPnLLayers,
    PortfolioRiskMeta,
    RiskLayerStats,
    RiskManagementROI,
    ScenarioRiskModel,
    SimulationResult,
)
from fhs.core.services.risk.delivery import DeliveryRiskService


def _feature(name: str, llp: float, cluster: str | None = None) -> Feature:
    return Feature(
        name=name,
        expected_users=12_000,
        conversion_rate=0.22,
        uncertainty=0.15,
        business_value_per_conversion=6.0,
        development_cost=45_000.0,
        annual_growth_rate=0.04,
        likelihood_of_non_delivery=llp,
        dependency_cluster=cluster,
    )


def _sim_result(name: str, mean: float, seed: int) -> SimulationResult:
    rng = np.random.default_rng(seed)
    scenarios = rng.normal(mean, mean * 0.05, 10_000)
    return SimulationResult(
        feature_name=name,
        results=scenarios,
        expected_value=float(np.mean(scenarios)),
        business_value_per_conversion=6.0,
        development_cost=45_000.0,
    )


def _risk_model() -> ScenarioRiskModel:
    return ScenarioRiskModel(
        risk_2_market_probability=0.20,
        risk_2_market_multiplier=0.85,
        risk_3_global_probability=0.05,
        risk_3_global_multiplier=0.60,
        component_risk_multiplier=0.70,
        default_component_probability=0.08,
        component_risk_by_cluster={
            "Cluster A": 0.08,
            "Cluster B": 0.12,
        },
    )


def test_stress_test_delivery_returns_zero_result_for_empty_selection() -> None:
    result = DeliveryRiskService.stress_test_delivery(
        selected=(),
        feature_by_name={},
        simulation_results={},
        risk_model=_risk_model(),
        scenarios=1_000,
        seed=42,
    )

    assert isinstance(result, DeliveryStressResult)
    assert result.expected_impact_eur == 0.0
    assert result.prob_success == 0.0


def test_stress_test_delivery_returns_positive_impact_for_selected_features() -> None:
    features = [
        _feature("A", 0.10, "Cluster A"),
        _feature("B", 0.20, "Cluster B"),
    ]
    feature_map = {feature.name: feature for feature in features}
    sim_results = {
        feature.name: _sim_result(feature.name, 1800.0 + idx * 150.0, idx + 1)
        for idx, feature in enumerate(features)
    }

    result = DeliveryRiskService.stress_test_delivery(
        selected=("A", "B"),
        feature_by_name=feature_map,
        simulation_results=sim_results,
        risk_model=_risk_model(),
        scenarios=5_000,
        seed=42,
    )

    assert isinstance(result, DeliveryStressResult)
    assert 0.0 <= result.prob_success <= 1.0
    assert 0.0 <= result.prob_failure <= 1.0
    assert result.expected_impact_eur > 0.0
    assert result.impact_cvar_95_eur >= result.impact_var_95_eur


def test_risk_management_assessment_and_pnl_assessment_return_typed_results() -> None:
    baseline = DeliveryStressResult(
        prob_success=0.3,
        prob_failure=0.7,
        expected_delay_weeks=8.0,
        expected_impact_eur=200_000.0,
        impact_var_95_eur=280_000.0,
        impact_cvar_95_eur=320_000.0,
    )
    managed = DeliveryStressResult(
        prob_success=0.5,
        prob_failure=0.5,
        expected_delay_weeks=6.0,
        expected_impact_eur=150_000.0,
        impact_var_95_eur=220_000.0,
        impact_cvar_95_eur=260_000.0,
    )

    roi = DeliveryRiskService.risk_management_assessment(
        {"Baseline": baseline, "Managed": managed},
        investment=500_000.0,
    )

    pnl_layers = PortfolioPnLLayers(
        base=RiskLayerStats(
            expected=50_000.0, var_95=10_000.0, cvar_95=5_000.0, std=1.0
        ),
        after_risk_1=RiskLayerStats(
            expected=40_000.0, var_95=5_000.0, cvar_95=2_000.0, std=1.0
        ),
        after_risk_2=RiskLayerStats(
            expected=35_000.0, var_95=2_000.0, cvar_95=1_000.0, std=1.0
        ),
        after_component=RiskLayerStats(
            expected=30_000.0, var_95=0.0, cvar_95=-2_000.0, std=1.0
        ),
        after_risk_3=RiskLayerStats(
            expected=25_000.0, var_95=-5_000.0, cvar_95=-8_000.0, std=1.0
        ),
        meta=PortfolioRiskMeta(
            market_hit_pct=0.1,
            global_hit_pct=0.02,
            cluster_hit_pct={},
            selected=("A",),
            risk_2_probability=0.2,
            risk_3_probability=0.05,
        ),
    )
    pnl = DeliveryRiskService.pnl_assessment(pnl_layers, investment=20_000.0)

    assert isinstance(roi, RiskManagementROI)
    assert roi.avoided_expected_loss_eur == 50_000.0
    assert isinstance(pnl, PnLAssessment)
    assert pnl.break_even_expected
