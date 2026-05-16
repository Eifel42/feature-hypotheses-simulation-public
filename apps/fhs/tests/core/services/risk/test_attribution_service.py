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

"""Tests for PortfolioRiskAttributionService."""

from __future__ import annotations

import numpy as np
import pytest

from fhs.core.model import Feature, ScenarioRiskModel, SimulationResult
from fhs.core.services.risk.attribution import PortfolioRiskAttributionService
from fhs.core.services.risk.calculator import RiskCalculator


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


def test_loss_metrics_and_shapley_are_consistent() -> None:
    features = [
        _feature("H1: A", 0.10, "Cluster A"),
        _feature("H2: B", 0.25, "Cluster B"),
    ]
    feature_by_name = {feature.name: feature for feature in features}
    simulation_results = {
        feature.name: _sim_result(feature.name, 1800.0 + idx * 200.0, idx + 1)
        for idx, feature in enumerate(features)
    }
    selected = [feature.name for feature in features]
    calculator = RiskCalculator()

    metrics = PortfolioRiskAttributionService.loss_metrics(
        selected=selected,
        feature_by_name=feature_by_name,
        simulation_results=simulation_results,
        risk_model=_risk_model(),
        confidence=0.95,
        seed=42,
        normalize_confidence=lambda x: x,
        loss_profile_function=lambda pnl, conf: calculator.loss_profile(
            pnl,
            confidence=conf,
        ),
    )

    shapley = PortfolioRiskAttributionService.risk_contributions_shapley(
        metric="cvar_loss",
        selected=selected,
        feature_by_name=feature_by_name,
        simulation_results=simulation_results,
        risk_model=_risk_model(),
        confidence=0.95,
        seed=42,
        normalize_confidence=lambda x: x,
        loss_profile_function=lambda pnl, conf: calculator.loss_profile(
            pnl,
            confidence=conf,
        ),
    )

    contribution_sum = sum(c.contribution_eur for c in shapley.contributions)
    assert metrics.investment == pytest.approx(60_000.0)
    assert 0.0 <= metrics.catastrophe_probability <= 1.0
    assert contribution_sum == pytest.approx(shapley.total_risk_eur, abs=1e-6)


def test_component_risk_summary_variants_return_typed_values() -> None:
    features = [
        _feature("H1: A", 0.10, "Cluster A"),
        _feature("H2: B", 0.25, "Cluster B"),
    ]
    feature_by_name = {feature.name: feature for feature in features}
    simulation_results = {
        feature.name: _sim_result(feature.name, 1800.0 + idx * 200.0, idx + 20)
        for idx, feature in enumerate(features)
    }
    selected = [feature.name for feature in features]

    summary = PortfolioRiskAttributionService.portfolio_component_risk_summary(
        selected=selected,
        feature_by_name=feature_by_name,
        simulation_results=simulation_results,
        normalized_risk_model=_risk_model(),
        clamp_probability=lambda value: float(max(0.0, min(0.95, value))),
    )

    summary_multi_year = (
        PortfolioRiskAttributionService.portfolio_component_risk_summary_multi_year(
            selected=selected,
            feature_by_name=feature_by_name,
            normalized_risk_model=_risk_model(),
            cluster_business_value_function=lambda feat_names: (
                float(
                    sum(
                        simulation_results[name].expected_business_value * 3
                        for name in feat_names
                    )
                ),
                float(
                    sum(
                        simulation_results[name].expected_business_value * 2.5
                        for name in feat_names
                    )
                ),
            ),
            clamp_probability=lambda value: float(max(0.0, min(0.95, value))),
        )
    )

    simulated = PortfolioRiskAttributionService.component_risk_simulated(
        selected=selected,
        feature_by_name=feature_by_name,
        simulation_results=simulation_results,
        risk_model=_risk_model(),
        confidence=0.95,
        seed=42,
        normalize_confidence=lambda x: x,
    )

    assert len(summary.cluster_risks) == 2
    assert len(summary_multi_year.cluster_risks) == 2
    assert len(simulated.cluster_risks) == 2
    assert 0.0 <= simulated.portfolio_component_probability <= 1.0
