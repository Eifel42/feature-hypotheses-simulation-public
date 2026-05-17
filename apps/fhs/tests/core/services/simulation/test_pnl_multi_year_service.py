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

"""Tests for PnLMultiYearService."""

from __future__ import annotations

from fhs.core.model import Feature, ScenarioRiskModel
from fhs.core.services.simulation.multi_year_pnl import PnLMultiYearService


def _feature(name: str, llp: float, cluster: str | None = None) -> Feature:
    return Feature(
        name=name,
        expected_users=12_000,
        conversion_rate=0.18,
        uncertainty=0.12,
        business_value_per_conversion=6.0,
        development_cost=40_000.0,
        annual_growth_rate=0.04,
        likelihood_of_non_delivery=llp,
        dependency_cluster=cluster,
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


def test_simulate_returns_empty_payload_for_unknown_features() -> None:
    service = PnLMultiYearService()
    feature_map = {"H1: A": _feature("H1: A", 0.10, "Cluster A")}

    result = service.simulate(
        ["Unknown"],
        feature_by_name=feature_map,
        risk_model=_risk_model(),
        years=3,
        scenarios=10_000,
        discount_rate=0.10,
        seed=42,
        service_seed=123,
    )

    assert result.investment == 0.0
    assert result.meta.selected == ()
    assert result.base.years == ()
    assert result.risk3.years == ()


def test_simulate_returns_multi_year_layers_and_probabilities() -> None:
    service = PnLMultiYearService()
    features = [
        _feature("H1: A", 0.10, "Cluster A"),
        _feature("H2: B", 0.25, "Cluster B"),
    ]
    feature_map = {feature.name: feature for feature in features}

    result = service.simulate(
        [feature.name for feature in features],
        feature_by_name=feature_map,
        risk_model=_risk_model(),
        years=3,
        scenarios=10_000,
        discount_rate=0.10,
        seed=42,
        service_seed=321,
    )

    assert result.investment == 80_000.0
    assert result.meta.selected == ("H1: A", "H2: B")
    assert result.meta.years == 3

    base_years = result.base.years
    assert len(base_years) == 3
    assert base_years[0].year == 1

    probabilities = result.meta.probabilities
    assert 0.0 <= probabilities.risk_2 <= 0.95
    assert 0.0 <= probabilities.risk_3 <= 0.95
    assert 0.0 <= probabilities.component_portfolio <= 1.0
