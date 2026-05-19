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

"""Tests for RiskLayerSimulationService."""

from __future__ import annotations

import numpy as np

from fhs.core.model import Feature, ScenarioRiskModel, SimulationResult
from fhs.core.services.risk.calculator import RiskCalculator
from fhs.core.services.risk.layer_simulation import RiskLayerSimulationService


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


def test_prepare_year1_state_builds_consistent_shapes() -> None:
    service = RiskLayerSimulationService(RiskCalculator())
    features = [
        _feature("H1: A", 0.10, "Cluster A"),
        _feature("H2: B", 0.25, "Cluster B"),
    ]
    results = {
        f.name: _sim_result(f.name, mean=2000.0 + idx * 300.0, seed=idx + 1)
        for idx, f in enumerate(features)
    }

    state = service.prepare_year1_state(
        features=features,
        sim_results=results,
        risk_model=_risk_model(),
        rng=np.random.default_rng(42),
    )

    assert state.selected == tuple(f.name for f in features)
    assert state.market_hits.shape == (10_000,)
    assert state.global_hits.shape == (10_000,)
    assert set(state.cluster_hits.keys()) == {"Cluster A", "Cluster B"}
    assert state.base_scenarios["H1: A"].shape == (10_000,)


def test_simulate_feature_layers_returns_profile_and_reduces_after_risk() -> None:
    service = RiskLayerSimulationService(RiskCalculator())
    feature = _feature("H1: A", 0.30, "Cluster A")
    sim_result = _sim_result(feature.name, mean=2100.0, seed=11)

    profile = service.simulate_feature_layers(
        feature=feature,
        sim_result=sim_result,
        risk_model=_risk_model(),
        seed=42,
    )

    assert profile.feature == feature.name
    assert profile.base.expected > 0
    assert profile.after_risk_3.expected <= profile.base.expected
    assert 0.0 <= profile.hit_rates.risk_1_blocked_pct <= 1.0


def test_simulate_portfolio_pnl_subtracts_investment_from_business_value_layers() -> (
    None
):
    service = RiskLayerSimulationService(RiskCalculator())
    features = [
        _feature("H1: A", 0.10, "Cluster A"),
        _feature("H2: B", 0.20, "Cluster B"),
    ]
    results = {
        f.name: _sim_result(f.name, mean=1800.0 + idx * 250.0, seed=idx + 20)
        for idx, f in enumerate(features)
    }
    model = _risk_model()

    business_value_layers = service.simulate_portfolio_layers(
        features=features,
        sim_results=results,
        risk_model=model,
        seed=42,
    )
    pnl_layers = service.simulate_portfolio_pnl(
        features=features,
        sim_results=results,
        risk_model=model,
        seed=42,
    )

    total_investment = sum(f.development_cost for f in features)
    assert (
        pnl_layers.base.expected
        == business_value_layers.base.expected - total_investment
    )
    assert pnl_layers.after_risk_3.expected == (
        business_value_layers.after_risk_3.expected - total_investment
    )
