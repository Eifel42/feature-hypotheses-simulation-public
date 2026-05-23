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

"""Tests for fhs.core.services.portfolio.utils — portfolio utility functions."""

import numpy as np
import pytest

from fhs.core.model import Feature, SimulationResult
from fhs.core.model.exceptions import InsufficientDataError
from fhs.core.services.portfolio.utils import (
    aggregate_portfolio_scenarios,
    aggregate_portfolio_scenarios_from_results,
    calculate_feature_contribution,
    calculate_portfolio_concentration,
)


@pytest.fixture
def features():
    return [
        Feature(
            name="A",
            expected_users=100,
            conversion_rate=0.5,
            uncertainty=0.2,
            business_value_per_conversion=10.0,
        ),
        Feature(
            name="B",
            expected_users=200,
            conversion_rate=0.3,
            uncertainty=0.1,
            business_value_per_conversion=5.0,
        ),
    ]


@pytest.fixture
def simulation_results():
    return {
        "A": SimulationResult(
            feature_name="A",
            results=np.array([50.0, 60.0, 70.0]),
            expected_value=60.0,
            business_value_per_conversion=10.0,
        ),
        "B": SimulationResult(
            feature_name="B",
            results=np.array([40.0, 50.0, 60.0]),
            expected_value=50.0,
            business_value_per_conversion=5.0,
        ),
    }


class TestAggregatePortfolioScenarios:
    def test_basic_aggregation(self, features, simulation_results):
        result = aggregate_portfolio_scenarios(simulation_results, features)
        # A: [50,60,70]*10 = [500,600,700]
        # B: [40,50,60]*5 = [200,250,300]
        # Sum = [700,850,1000]
        np.testing.assert_array_almost_equal(result, [700.0, 850.0, 1000.0])

    def test_missing_feature_skipped(self, simulation_results):
        features = [
            Feature(
                name="A",
                expected_users=100,
                conversion_rate=0.5,
                uncertainty=0.2,
                business_value_per_conversion=10.0,
            ),
            Feature(
                name="C", expected_users=100, conversion_rate=0.5, uncertainty=0.2
            ),  # not in results
        ]
        result = aggregate_portfolio_scenarios(simulation_results, features)
        np.testing.assert_array_almost_equal(result, [500.0, 600.0, 700.0])

    def test_empty_features_raises(self, simulation_results):
        with pytest.raises(InsufficientDataError):
            aggregate_portfolio_scenarios(simulation_results, [])

    def test_no_matching_features_raises(self):
        features = [
            Feature(name="X", expected_users=100, conversion_rate=0.5, uncertainty=0.2)
        ]
        results = {"Y": SimulationResult(feature_name="Y", results=np.array([1.0]))}
        with pytest.raises(InsufficientDataError):
            aggregate_portfolio_scenarios(results, features)


class TestAggregateFromResults:
    def test_basic(self, simulation_results):
        result = aggregate_portfolio_scenarios_from_results(simulation_results)
        # A: [50,60,70]*10 = [500,600,700]
        # B: [40,50,60]*5 = [200,250,300]
        np.testing.assert_array_almost_equal(result, [700.0, 850.0, 1000.0])

    def test_empty_raises(self):
        with pytest.raises(InsufficientDataError):
            aggregate_portfolio_scenarios_from_results({})


class TestCalculateFeatureContribution:
    def test_normal(self, features, simulation_results):
        contribution = calculate_feature_contribution(
            features[0], simulation_results["A"], portfolio_total=850.0
        )
        # A expected_business_value = 60 * 10 = 600
        expected = (600.0 / 850.0) * 100
        assert abs(contribution - expected) < 0.01

    def test_zero_portfolio(self, features, simulation_results):
        assert (
            calculate_feature_contribution(
                features[0], simulation_results["A"], portfolio_total=0.0
            )
            == 0.0
        )


class TestCalculatePortfolioConcentration:
    def test_normal(self, features, simulation_results):
        conc = calculate_portfolio_concentration(features, simulation_results)
        assert "A" in conc
        assert "B" in conc
        assert abs(sum(conc.values()) - 1.0) < 1e-6

    def test_zero_value_portfolio(self):
        features = [
            Feature(name="X", expected_users=100, conversion_rate=0.5, uncertainty=0.2),
            Feature(name="Y", expected_users=100, conversion_rate=0.5, uncertainty=0.2),
        ]
        results = {
            "X": SimulationResult(
                feature_name="X", expected_value=0.0, business_value_per_conversion=0.0
            ),
            "Y": SimulationResult(
                feature_name="Y", expected_value=0.0, business_value_per_conversion=0.0
            ),
        }
        conc = calculate_portfolio_concentration(features, results)
        assert conc["X"] == 0.5
        assert conc["Y"] == 0.5
