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

"""Tests for PortfolioMultiYearService."""

from __future__ import annotations

from fhs.core.model import Feature, MultiYearResult
from fhs.core.services.simulation.portfolio_multi_year import PortfolioMultiYearService


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


def test_simulate_returns_empty_result_for_unknown_selection() -> None:
    feature_map = {"H1: A": _feature("H1: A", 0.10, "Cluster A")}

    result = PortfolioMultiYearService.simulate(
        selected=("Unknown",),
        feature_by_name=feature_map,
        years=3,
        scenarios=2_000,
        discount_rate=0.10,
        seed=42,
    )

    assert isinstance(result, MultiYearResult)
    assert result.feature_name == "Empty Portfolio"
    assert result.years == []


def test_simulate_aggregates_year_results_for_selected_features() -> None:
    features = [
        _feature("H1: A", 0.10, "Cluster A"),
        _feature("H2: B", 0.25, "Cluster B"),
    ]
    feature_map = {feature.name: feature for feature in features}

    result = PortfolioMultiYearService.simulate(
        selected=("H1: A", "H2: B"),
        feature_by_name=feature_map,
        years=3,
        scenarios=2_000,
        discount_rate=0.10,
        seed=42,
    )

    assert isinstance(result, MultiYearResult)
    assert result.feature_name == "Selected Portfolio"
    assert len(result.years) == 3
    assert result.years[0].year == 1
    assert result.years[2].year == 3
    assert result.years[0].var_95 <= result.years[0].expected
