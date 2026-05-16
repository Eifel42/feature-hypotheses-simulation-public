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

"""Tests for PortfolioLayerRiskService."""

from __future__ import annotations

import numpy as np

from fhs.core.model import Feature, ScenarioRiskModel, SimulationResult
from fhs.core.services.risk.portfolio_layers import PortfolioLayerRiskService


def _feature(name: str, llp: float, cluster: str | None = None) -> Feature:
    return Feature(
        name=name,
        expected_users=10_000,
        conversion_rate=0.20,
        uncertainty=0.10,
        business_value_per_conversion=5.0,
        development_cost=30_000.0,
        annual_growth_rate=0.05,
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
        business_value_per_conversion=5.0,
        development_cost=30_000.0,
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


def test_normalize_risk_model_clamps_values() -> None:
    normalized = PortfolioLayerRiskService.normalize_risk_model(
        {
            "risk_2_market_probability": 1.2,
            "risk_2_market_multiplier": -1.0,
            "risk_3_global_probability": -0.5,
            "risk_3_global_multiplier": 2.0,
            "default_component_probability": 1.4,
            "component_risk_by_cluster": {"Cluster A": -0.2, "Cluster B": 1.6},
        }
    )

    assert normalized.risk_2_market_probability == 0.95
    assert normalized.risk_2_market_multiplier == 0.0
    assert normalized.risk_3_global_probability == 0.0
    assert normalized.risk_3_global_multiplier == 1.0
    assert normalized.default_component_probability == 0.95
    assert normalized.component_risk_by_cluster["Cluster A"] == 0.0
    assert normalized.component_risk_by_cluster["Cluster B"] == 0.95


def test_simulate_feature_risk_layers_supports_probability_overrides() -> None:
    feature = _feature("H1: A", 0.30, "Cluster A")
    feature_by_name = {feature.name: feature}
    simulation_results = {feature.name: _sim_result(feature.name, 2100.0, 11)}

    profile = PortfolioLayerRiskService.simulate_feature_risk_layers(
        feature.name,
        feature_by_name=feature_by_name,
        simulation_results=simulation_results,
        risk_model=_risk_model(),
        risk1_probability=0.0,
        risk2_probability=0.0,
        risk3_probability=0.0,
        component_probability=0.0,
        seed=42,
    )

    assert profile.hit_rates.risk_1_blocked_pct == 0.0
    assert profile.hit_rates.risk_2_hit_pct == 0.0
    assert profile.hit_rates.risk_3_hit_pct == 0.0
    assert profile.hit_rates.component_hit_pct == 0.0
    assert profile.after_risk_3.expected == profile.base.expected


def test_simulate_portfolio_pnl_layers_and_sensitivity_return_typed_data() -> None:
    features = [
        _feature("H1: A", 0.10, "Cluster A"),
        _feature("H2: B", 0.20, "Cluster B"),
    ]
    feature_by_name = {f.name: f for f in features}
    simulation_results = {
        f.name: _sim_result(f.name, mean=1800.0 + idx * 250.0, seed=idx + 20)
        for idx, f in enumerate(features)
    }
    selected = [f.name for f in features]

    pnl_layers = PortfolioLayerRiskService.simulate_portfolio_pnl_layers(
        selected=selected,
        feature_by_name=feature_by_name,
        simulation_results=simulation_results,
        risk_model=_risk_model(),
        seed=42,
    )
    sensitivity = PortfolioLayerRiskService.portfolio_sensitivity(
        selected=selected,
        feature_by_name=feature_by_name,
        simulation_results=simulation_results,
        risk_model=_risk_model(),
        seed=42,
    )

    assert pnl_layers.meta.selected == tuple(selected)
    assert len(sensitivity) == 9
    assert all(row.var_95 <= row.expected for row in sensitivity)


def test_risk1_factor_scales_delivery_risk() -> None:
    """risk1_factor=0.0 eliminates delivery risk; factor=2.0 doubles it."""
    features = [
        _feature("H1: A", 0.30, "Cluster A"),
        _feature("H2: B", 0.20, "Cluster B"),
    ]
    feature_by_name = {f.name: f for f in features}
    simulation_results = {
        f.name: _sim_result(f.name, mean=2000.0, seed=idx + 30)
        for idx, f in enumerate(features)
    }
    selected = [f.name for f in features]

    base = PortfolioLayerRiskService.simulate_portfolio_risk_layers(
        selected=selected,
        feature_by_name=feature_by_name,
        simulation_results=simulation_results,
        risk_model=_risk_model(),
        seed=42,
    )

    no_delivery_risk = PortfolioLayerRiskService.simulate_portfolio_risk_layers(
        selected=selected,
        feature_by_name=feature_by_name,
        simulation_results=simulation_results,
        risk_model=_risk_model(),
        risk1_factor=0.0,
        seed=42,
    )

    double_delivery_risk = PortfolioLayerRiskService.simulate_portfolio_risk_layers(
        selected=selected,
        feature_by_name=feature_by_name,
        simulation_results=simulation_results,
        risk_model=_risk_model(),
        risk1_factor=2.0,
        seed=42,
    )

    # No delivery risk → after_risk_1 == base (no loss at delivery gate)
    assert no_delivery_risk.after_risk_1.expected == no_delivery_risk.base.expected

    # More delivery risk → lower expected value after risk 1
    assert double_delivery_risk.after_risk_1.expected < base.after_risk_1.expected

    # Final value ordering: no_risk > base > double_risk
    assert no_delivery_risk.after_risk_3.expected > base.after_risk_3.expected
    assert base.after_risk_3.expected > double_delivery_risk.after_risk_3.expected
