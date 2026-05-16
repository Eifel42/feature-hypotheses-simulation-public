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

"""Tests for OperatingCostResult and FeatureOperatingCostStats value objects."""

import numpy as np
import pytest

from fhs.core.model.value_objects.operating_cost import (
    FeatureOperatingCostStats,
    OperatingCostResult,
)


def _make_stats(
    name: str = "Feature A",
    base: float = 10_000.0,
    expected: float = 11_250.0,
    worst: float = 12_500.0,
    n: int = 100,
    inflation_max: float = 0.25,
) -> FeatureOperatingCostStats:
    scenarios = base * (1.0 + np.linspace(0.0, inflation_max, n))
    return FeatureOperatingCostStats(
        feature_name=name,
        base_annual_cost=base,
        expected_cost=expected,
        worst_case_cost=worst,
        scenarios=scenarios,
    )


class TestFeatureOperatingCostStats:
    def test_cost_uplift_is_difference(self):
        stats = _make_stats(base=10_000.0, worst=12_500.0)
        assert stats.cost_uplift_eur == pytest.approx(2_500.0)

    def test_cost_uplift_zero_when_no_inflation(self):
        stats = _make_stats(base=5_000.0, worst=5_000.0, inflation_max=0.0)
        assert stats.cost_uplift_eur == pytest.approx(0.0)

    def test_scenarios_shape(self):
        stats = _make_stats(n=200)
        assert stats.scenarios.shape == (200,)

    def test_frozen_dataclass(self):
        stats = _make_stats()
        with pytest.raises(Exception):
            stats.base_annual_cost = 99_000.0  # type: ignore[misc]

    def test_base_cost_stored_correctly(self):
        stats = _make_stats(base=25_000.0)
        assert stats.base_annual_cost == 25_000.0

    def test_worst_case_geq_base(self):
        stats = _make_stats(base=10_000.0, worst=12_500.0)
        assert stats.worst_case_cost >= stats.base_annual_cost


class TestOperatingCostResult:
    @staticmethod
    def _make_result(inflation_max: float = 0.25) -> OperatingCostResult:
        n = 1_000
        inflation_scenarios = np.random.default_rng(42).uniform(0.0, inflation_max, n)
        stats_a = _make_stats(
            "Feature A", base=10_000.0, worst=10_000.0 * (1 + inflation_max)
        )
        stats_b = _make_stats(
            "Feature B", base=20_000.0, worst=20_000.0 * (1 + inflation_max)
        )
        return OperatingCostResult(
            inflation_max=inflation_max,
            inflation_scenarios=inflation_scenarios,
            per_feature={"Feature A": stats_a, "Feature B": stats_b},
        )

    def test_portfolio_base_cost_is_sum(self):
        result = self._make_result()
        assert result.portfolio_base_cost == pytest.approx(30_000.0)

    def test_portfolio_worst_case_cost_is_sum(self):
        result = self._make_result(inflation_max=0.25)
        assert result.portfolio_worst_case_cost == pytest.approx(37_500.0)

    def test_portfolio_expected_cost_is_sum_of_expected(self):
        result = self._make_result()
        expected = (
            result.per_feature["Feature A"].expected_cost
            + result.per_feature["Feature B"].expected_cost
        )
        assert result.portfolio_expected_cost == pytest.approx(expected)

    def test_expected_inflation_pct_range(self):
        result = self._make_result(inflation_max=0.25)
        # Uniform(0, 0.25) mean ≈ 12.5%; allow some sampling noise
        assert 10.0 <= result.expected_inflation_pct <= 15.0

    def test_inflation_max_stored(self):
        result = self._make_result(inflation_max=0.30)
        assert result.inflation_max == pytest.approx(0.30)

    def test_per_feature_keys_match(self):
        result = self._make_result()
        assert set(result.per_feature.keys()) == {"Feature A", "Feature B"}

    def test_frozen_dataclass(self):
        result = self._make_result()
        with pytest.raises(Exception):
            result.inflation_max = 0.99  # type: ignore[misc]

    def test_zero_inflation_max(self):
        n = 100
        inflation_scenarios = np.zeros(n)
        stats = _make_stats(
            "F", base=5_000.0, expected=5_000.0, worst=5_000.0, inflation_max=0.0
        )
        result = OperatingCostResult(
            inflation_max=0.0,
            inflation_scenarios=inflation_scenarios,
            per_feature={"F": stats},
        )
        assert result.portfolio_base_cost == pytest.approx(5_000.0)
        assert result.portfolio_worst_case_cost == pytest.approx(5_000.0)
        assert result.expected_inflation_pct == pytest.approx(0.0)
