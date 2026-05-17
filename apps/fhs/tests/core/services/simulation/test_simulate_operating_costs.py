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

"""Tests for FeatureSimulator.simulate_operating_costs()."""

import numpy as np
import pytest

from fhs.core.model import Feature
from fhs.core.model.value_objects.operating_cost import (
    OperatingCostResult,
)
from fhs.core.services import FeatureSimulator


def _feature(name: str, annual_operating_cost: float = 10_000.0) -> Feature:
    return Feature(
        name=name,
        expected_users=1_000,
        conversion_rate=0.1,
        uncertainty=0.2,
        annual_operating_cost=annual_operating_cost,
    )


class TestSimulateOperatingCosts:
    def setup_method(self):
        self.simulator = FeatureSimulator(seed=42)

    def test_returns_operating_cost_result(self):
        features = [_feature("A", 10_000.0)]
        result = self.simulator.simulate_operating_costs(features, scenarios=500)
        assert isinstance(result, OperatingCostResult)

    def test_per_feature_key_is_feature_name(self):
        features = [_feature("Alpha"), _feature("Beta")]
        result = self.simulator.simulate_operating_costs(features, scenarios=500)
        assert "Alpha" in result.per_feature
        assert "Beta" in result.per_feature

    def test_inflation_scenarios_shape(self):
        features = [_feature("A")]
        result = self.simulator.simulate_operating_costs(features, scenarios=300)
        assert result.inflation_scenarios.shape == (300,)

    def test_inflation_scenarios_within_bounds(self):
        inflation_max = 0.25
        features = [_feature("A")]
        result = self.simulator.simulate_operating_costs(
            features, cost_inflation_max=inflation_max, scenarios=1_000
        )
        assert float(np.min(result.inflation_scenarios)) >= 0.0
        assert float(np.max(result.inflation_scenarios)) <= inflation_max

    def test_base_cost_matches_feature_config(self):
        features = [_feature("A", annual_operating_cost=15_000.0)]
        result = self.simulator.simulate_operating_costs(features, scenarios=500)
        assert result.per_feature["A"].base_annual_cost == pytest.approx(15_000.0)

    def test_worst_case_equals_base_times_one_plus_max(self):
        base = 8_000.0
        inflation_max = 0.20
        features = [_feature("A", annual_operating_cost=base)]
        result = self.simulator.simulate_operating_costs(
            features, cost_inflation_max=inflation_max, scenarios=500
        )
        assert result.per_feature["A"].worst_case_cost == pytest.approx(
            base * (1 + inflation_max)
        )

    def test_expected_cost_between_base_and_worst_case(self):
        features = [_feature("A", annual_operating_cost=12_000.0)]
        result = self.simulator.simulate_operating_costs(
            features, cost_inflation_max=0.25, scenarios=2_000
        )
        stats = result.per_feature["A"]
        assert stats.base_annual_cost <= stats.expected_cost <= stats.worst_case_cost

    def test_feature_scenarios_shape_matches_n_scenarios(self):
        features = [_feature("A")]
        n = 400
        result = self.simulator.simulate_operating_costs(features, scenarios=n)
        assert result.per_feature["A"].scenarios.shape == (n,)

    def test_zero_operating_cost_feature(self):
        features = [_feature("Free", annual_operating_cost=0.0)]
        result = self.simulator.simulate_operating_costs(features, scenarios=500)
        stats = result.per_feature["Free"]
        assert stats.base_annual_cost == pytest.approx(0.0)
        assert stats.worst_case_cost == pytest.approx(0.0)
        assert float(np.sum(stats.scenarios)) == pytest.approx(0.0)

    def test_portfolio_base_cost_is_sum(self):
        features = [_feature("A", 5_000.0), _feature("B", 15_000.0)]
        result = self.simulator.simulate_operating_costs(features, scenarios=500)
        assert result.portfolio_base_cost == pytest.approx(20_000.0)

    def test_portfolio_worst_case_is_sum(self):
        inflation_max = 0.25
        features = [_feature("A", 5_000.0), _feature("B", 15_000.0)]
        result = self.simulator.simulate_operating_costs(
            features, cost_inflation_max=inflation_max, scenarios=500
        )
        assert result.portfolio_worst_case_cost == pytest.approx(
            20_000.0 * (1 + inflation_max)
        )

    def test_shared_inflation_factor(self):
        """All features must see the same per-scenario inflation draw."""
        features = [_feature("A", 10_000.0), _feature("B", 10_000.0)]
        result = self.simulator.simulate_operating_costs(features, scenarios=500)
        # If inflation is shared, A and B scenarios should have identical ratios
        ratio_a = result.per_feature["A"].scenarios / 10_000.0 - 1.0
        ratio_b = result.per_feature["B"].scenarios / 10_000.0 - 1.0
        np.testing.assert_allclose(ratio_a, ratio_b, rtol=1e-9)

    def test_inflation_max_stored_in_result(self):
        features = [_feature("A")]
        result = self.simulator.simulate_operating_costs(
            features, cost_inflation_max=0.30, scenarios=100
        )
        assert result.inflation_max == pytest.approx(0.30)

    def test_empty_feature_list(self):
        result = self.simulator.simulate_operating_costs([], scenarios=100)
        assert isinstance(result, OperatingCostResult)
        assert result.per_feature == {}
        assert result.portfolio_base_cost == pytest.approx(0.0)
