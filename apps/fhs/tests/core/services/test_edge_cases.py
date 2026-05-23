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

"""
Edge case tests for robustness of core FHS modules.

Covers NaN/Inf propagation, empty inputs, boundary values,
and numerical stability edge cases.
"""

import numpy as np
import pytest

from fhs.core.model import Feature, SimulationResult
from fhs.core.model.exceptions import SimulationError
from fhs.core.services import (
    FeatureSimulator,
    PortfolioRiskAnalyzer,
    RiskCalculator,
)
from fhs.core.services.monte_carlo import MonteCarloEngine


class TestRiskCalculatorEdgeCases:
    """Edge cases for RiskCalculator."""

    def setup_method(self):
        self.calc = RiskCalculator()

    def test_var_with_two_element_array(self):
        """VaR should work with minimal dataset."""
        data = np.array([1.0, 2.0])
        var = self.calc.calculate_var(data, confidence_level=0.95)
        assert np.isfinite(var)

    def test_cvar_with_two_element_array(self):
        """CVaR should work with minimal dataset."""
        data = np.array([1.0, 2.0])
        cvar = self.calc.calculate_cvar(data, confidence_level=0.95)
        assert np.isfinite(cvar)

    def test_var_with_identical_values(self):
        """VaR with zero variance should return that value."""
        data = np.array([5.0] * 100)
        var = self.calc.calculate_var(data, confidence_level=0.95)
        assert var == pytest.approx(5.0)

    def test_cvar_less_than_or_equal_var(self):
        """CVaR (expected shortfall) must be <= VaR for loss distributions."""
        rng = np.random.default_rng(42)
        data = rng.normal(100, 20, 10000)
        var = self.calc.calculate_var(data, confidence_level=0.95)
        cvar = self.calc.calculate_cvar(data, confidence_level=0.95)
        assert cvar <= var

    def test_percentile_at_boundaries(self):
        """Percentile at 0 and 100 should return min/max."""
        data = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        p0 = self.calc.calculate_percentile(data, 0)
        p100 = self.calc.calculate_percentile(data, 100)
        assert p0 == pytest.approx(10.0, abs=1.0)
        assert p100 == pytest.approx(50.0, abs=1.0)

    def test_bootstrap_with_small_sample(self):
        """Bootstrap CI with very small sample."""
        data = np.array([1.0, 2.0, 3.0])
        lower, upper = self.calc.bootstrap_confidence_interval(
            data, n_bootstrap=100, confidence_level=0.95
        )
        assert lower <= upper
        assert np.isfinite(lower)
        assert np.isfinite(upper)


class TestMonteCarloEdgeCases:
    """Edge cases for MonteCarloEngine."""

    def setup_method(self):
        self.engine = MonteCarloEngine(seed=42)

    def test_simulate_zero_uncertainty(self):
        """Zero uncertainty should return deterministic results."""
        feature = Feature(
            name="Stable",
            expected_users=1000,
            conversion_rate=0.5,
            uncertainty=0.0,
        )
        results = self.engine.simulate(feature, scenarios=1000)
        assert len(set(results)) == 1

    def test_simulate_max_uncertainty(self):
        """Maximum uncertainty should still produce valid results."""
        feature = Feature(
            name="Chaotic",
            expected_users=1000,
            conversion_rate=0.5,
            uncertainty=1.0,
        )
        results = self.engine.simulate(feature, scenarios=5000)
        assert all(np.isfinite(results))

    def test_simulate_min_conversion_rate(self):
        """Minimum conversion rate (near zero)."""
        feature = Feature(
            name="LowConv",
            expected_users=1000,
            conversion_rate=0.0001,
            uncertainty=0.05,
        )
        results = self.engine.simulate(feature, scenarios=1000)
        assert all(np.isfinite(results))

    def test_bounded_lower_equals_upper(self):
        """Bounded simulation with equal bounds returns constant."""
        feature = Feature(
            name="Fixed",
            expected_users=100,
            conversion_rate=0.5,
            uncertainty=0.1,
        )
        results = self.engine.simulate_bounded(
            feature, scenarios=1000, lower_bound=0.3, upper_bound=0.3
        )
        np.testing.assert_allclose(results, 0.3)


class TestSimulationResultEdgeCases:
    """Edge cases for SimulationResult."""

    def test_negative_expected_value(self):
        """SimulationResult with negative expected value."""
        sr = SimulationResult(
            feature_name="Loss",
            results=np.array([-100.0, -50.0, 0.0, 50.0]),
            expected_value=-25.0,
        )
        assert sr.expected_value == -25.0

    def test_zero_development_cost_roi(self):
        """ROI with zero development cost should return 0."""
        sr = SimulationResult(
            feature_name="Free",
            results=np.array([100.0, 200.0]),
            expected_value=150.0,
            development_cost=0.0,
        )
        assert sr.roi == 0.0

    def test_single_result(self):
        """SimulationResult with a single data point."""
        sr = SimulationResult(
            feature_name="Single",
            results=np.array([42.0]),
            expected_value=42.0,
        )
        assert sr.expected_value == 42.0
        assert len(sr.results_array) == 1

    def test_large_result_set(self):
        """SimulationResult with large dataset."""
        rng = np.random.default_rng(42)
        data = rng.normal(1000, 100, 100_000)
        sr = SimulationResult(
            feature_name="Big",
            results=data,
            expected_value=float(np.mean(data)),
        )
        assert len(sr.results_array) == 100_000
        assert sr.expected_value == pytest.approx(1000, rel=0.01)


class TestPortfolioEdgeCases:
    """Edge cases for PortfolioRiskAnalyzer."""

    @staticmethod
    def _make_result(name, data):
        return SimulationResult(
            feature_name=name,
            results=np.array(data),
            expected_value=float(np.mean(data)),
        )

    def test_single_feature_portfolio(self):
        """Portfolio with only one feature."""
        analyzer = PortfolioRiskAnalyzer(seed=42)
        rng = np.random.default_rng(42)
        results = {
            "Only": self._make_result("Only", rng.normal(100, 10, 1000)),
        }
        risk = analyzer.calculate_portfolio_risk(results)
        assert np.isfinite(risk.portfolio_metrics.var_95)

    def test_identical_features_portfolio(self):
        """Portfolio with identical features (perfect correlation)."""
        analyzer = PortfolioRiskAnalyzer(seed=42)
        data = np.random.default_rng(42).normal(100, 10, 1000)
        results = {
            "A": self._make_result("A", data.copy()),
            "B": self._make_result("B", data.copy()),
        }
        risk = analyzer.calculate_portfolio_risk(results)
        assert np.isfinite(risk.portfolio_metrics.var_95)
        # Diversification should be minimal with identical features
        assert risk.diversification.diversification_ratio == (
            pytest.approx(0.0, abs=0.05)
        )

    def test_portfolio_unnormalized_weights(self):
        """Weights that don't sum to 1 should be auto-normalized."""
        analyzer = PortfolioRiskAnalyzer(seed=42)
        rng = np.random.default_rng(42)
        results = {
            "A": self._make_result("A", rng.normal(100, 10, 1000)),
            "B": self._make_result("B", rng.normal(200, 20, 1000)),
        }
        weights = {"A": 3.0, "B": 7.0}
        risk = analyzer.calculate_portfolio_risk(results, weights=weights)
        assert np.isfinite(risk.portfolio_metrics.var_95)

    def test_single_feature_correlation_matrix(self):
        """Correlation matrix with a single feature raises or returns 1×1."""
        analyzer = PortfolioRiskAnalyzer(seed=42)
        rng = np.random.default_rng(42)
        results = {
            "Solo": self._make_result("Solo", rng.normal(100, 10, 1000)),
        }
        # Single-feature correlation is degenerate — library raises IndexError
        # because np.corrcoef returns a scalar for 1-d input.
        # This documents the known edge case.
        with pytest.raises((IndexError, ValueError)):
            analyzer.calculate_correlation_matrix(results)

    def test_stress_test_zero_multiplier(self):
        """Stress test with zero multiplier (total loss scenario)."""
        analyzer = PortfolioRiskAnalyzer(seed=42)
        rng = np.random.default_rng(42)
        results = {
            "A": self._make_result("A", rng.normal(100, 10, 1000)),
        }
        stress = analyzer.stress_test_portfolio(
            results,
            scenarios=[{"A": 0.0}],
        )
        # With a 0× multiplier all values should be zero
        scenario = stress["stress_scenarios"][0]
        assert scenario["stressed_metrics"]["expected_value"] == pytest.approx(
            0.0, abs=0.01
        )


class TestSimulatorEdgeCases:
    """Edge cases for FeatureSimulator."""

    def test_seed_reproducibility(self):
        """Same seed must produce identical results."""
        feature = Feature(
            name="Test",
            expected_users=1000,
            conversion_rate=0.3,
            uncertainty=0.2,
        )
        r1 = FeatureSimulator(seed=123).simulate_feature(feature)
        r2 = FeatureSimulator(seed=123).simulate_feature(feature)
        np.testing.assert_array_equal(r1.results_array, r2.results_array)

    def test_different_seeds_differ(self):
        """Different seeds must produce different results."""
        feature = Feature(
            name="Test",
            expected_users=1000,
            conversion_rate=0.3,
            uncertainty=0.2,
        )
        r1 = FeatureSimulator(seed=1).simulate_feature(feature)
        r2 = FeatureSimulator(seed=2).simulate_feature(feature)
        assert not np.array_equal(r1.results_array, r2.results_array)


class TestCoverageGaps:
    """Tests to cover remaining uncovered lines."""

    def test_correlated_simulation_non_finite_error(self):
        """Correlated simulation raises on non-finite values (monte_carlo.py:296)."""
        engine = MonteCarloEngine(seed=42)

        features = [
            Feature(
                name="A",
                expected_users=1000,
                conversion_rate=0.5,
                uncertainty=0.3,
            ),
            Feature(
                name="B",
                expected_users=1000,
                conversion_rate=0.5,
                uncertainty=0.3,
            ),
        ]
        corr = np.array([[1.0, 0.5], [0.5, 1.0]])

        # Replace engine.rng with a wrapper that returns Inf from
        # multivariate_normal to trigger the non-finite check.
        import unittest.mock as mock

        original_rng = engine.rng

        mock_rng = mock.MagicMock(wraps=original_rng)
        mock_rng.multivariate_normal = mock.MagicMock(
            side_effect=lambda *a, **kw: np.full(
                (kw.get("size", 1000), len(features)), np.inf
            )
        )
        engine.rng = mock_rng

        with pytest.raises(SimulationError, match="non-finite"):
            engine.simulate_correlated(features, corr, 1000)

        engine.rng = original_rng
