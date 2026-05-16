# Project: FHS (Feature Hypotheses Simulation)
# Copyright: Eifel42 Stefan Zils 2026
# License: See LICENSE and README.md

"""Targeted tests for residual branch coverage gaps in portfolio services."""

from __future__ import annotations

from fhs.core.model import Feature
from fhs.core.services.portfolio.analysis import PortfolioRiskAnalyzer
from fhs.core.services.simulation import FeatureSimulator


def _build_results():
    features = [
        Feature(
            name="Premium",
            expected_users=5000,
            conversion_rate=0.25,
            uncertainty=0.15,
        ),
        Feature(
            name="Basic",
            expected_users=15000,
            conversion_rate=0.08,
            uncertainty=0.10,
        ),
    ]
    simulator = FeatureSimulator(seed=42)
    return {f.name: simulator.simulate_feature(f, scenarios=1000) for f in features}


def test_stress_test_portfolio_with_explicit_weights():
    """Cover branch in analysis.stress_test_portfolio where weights is provided."""
    analyzer = PortfolioRiskAnalyzer(seed=42)
    results = _build_results()
    weights = {"Premium": 0.7, "Basic": 0.3}

    stress_test = analyzer.stress_test_portfolio(results, weights=weights)

    assert "baseline_metrics" in stress_test
    assert "stress_scenarios" in stress_test
    assert len(stress_test["stress_scenarios"]) > 0
