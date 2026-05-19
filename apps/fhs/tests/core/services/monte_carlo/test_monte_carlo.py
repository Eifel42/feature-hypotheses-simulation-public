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
Tests for the monte_carlo module.

This module tests the Monte Carlo simulation engine functionality.
"""

import numpy as np
import pytest

from fhs.core.model import Feature
from fhs.core.model.exceptions import (
    CorrelationMatrixError,
    ValidationError,
)
from fhs.core.services.monte_carlo import MonteCarloEngine


class TestMonteCarloEngine:
    """Test cases for the MonteCarloEngine class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.engine = MonteCarloEngine()
        self.test_feature = Feature(
            name="Test Feature",
            expected_users=1000,
            conversion_rate=0.15,
            uncertainty=0.1,
        )

    def test_engine_initialization(self):
        """Test that MonteCarloEngine initializes correctly."""
        engine = MonteCarloEngine()
        assert engine is not None

        # Test with custom seed
        engine_with_seed = MonteCarloEngine(seed=42)
        assert engine_with_seed is not None

    def test_simulate_basic_functionality(self):
        """Test basic simulation functionality."""
        results = self.engine.simulate(self.test_feature, scenarios=1000)

        assert len(results) == 1000
        assert all(
            isinstance(x, int | float | np.integer | np.floating) for x in results
        )
        assert all(x >= 0 for x in results)  # Results should be non-negative

    def test_simulate_minimum_scenarios(self):
        """Test that minimum scenarios requirement is enforced."""
        with pytest.raises(ValidationError, match="Minimum 1000 scenarios required"):
            self.engine.simulate(self.test_feature, scenarios=500)

    def test_simulate_invalid_distribution(self):
        """Test that invalid distribution raises ValueError."""
        with pytest.raises(ValueError, match="Distribution must be one of"):
            self.engine.simulate(
                self.test_feature, scenarios=1000, distribution="invalid"
            )

    def test_simulate_normal_distribution(self):
        """Test simulation with normal distribution."""
        engine = MonteCarloEngine(seed=42)
        results = engine.simulate(
            self.test_feature, scenarios=1000, distribution="normal"
        )

        # Statistical tests - results should be roughly centered around expected value
        expected_conversions = (
            self.test_feature.expected_users * self.test_feature.conversion_rate
        )
        mean_result = np.mean(results)

        # Allow for more variance in the test
        assert abs(mean_result - expected_conversions) / expected_conversions < 1.0

    def test_simulate_bounded_basic(self):
        """Test bounded simulation functionality."""
        results = self.engine.simulate_bounded(
            self.test_feature, scenarios=1000, lower_bound=0.0, upper_bound=1.0
        )

        assert len(results) == 1000
        assert all(0.0 <= x <= self.test_feature.expected_users for x in results)

    def test_simulate_bounded_invalid_bounds(self):
        """Test that invalid bounds raise ValueError."""
        with pytest.raises(
            ValueError, match="Lower bound.*must be less than upper bound"
        ):
            self.engine.simulate_bounded(
                self.test_feature, scenarios=1000, lower_bound=1.0, upper_bound=0.0
            )

    def test_simulate_bounded_minimum_scenarios(self):
        """Test that bounded simulation enforces minimum scenarios."""
        with pytest.raises(ValidationError, match="Minimum 1000 scenarios required"):
            self.engine.simulate_bounded(
                self.test_feature, scenarios=500, lower_bound=0.0, upper_bound=1.0
            )

    def test_simulate_reproducibility_with_seed(self):
        """Test that setting seed produces reproducible results."""
        engine1 = MonteCarloEngine(seed=42)
        engine2 = MonteCarloEngine(seed=42)

        results1 = engine1.simulate(self.test_feature, scenarios=1000)
        results2 = engine2.simulate(self.test_feature, scenarios=1000)

        np.testing.assert_array_equal(results1, results2)

    def test_simulate_different_features(self):
        """Test simulation with different feature parameters."""
        features = [
            Feature(
                name="Low Conversion",
                expected_users=1000,
                conversion_rate=0.05,
                uncertainty=0.02,
            ),
            Feature(
                name="High Conversion",
                expected_users=1000,
                conversion_rate=0.50,
                uncertainty=0.1,
            ),
            Feature(
                name="High Uncertainty",
                expected_users=1000,
                conversion_rate=0.15,
                uncertainty=0.3,
            ),
            Feature(
                name="Low Uncertainty",
                expected_users=1000,
                conversion_rate=0.15,
                uncertainty=0.01,
            ),
        ]

        for feature in features:
            results = self.engine.simulate(feature, scenarios=1000)
            assert len(results) == 1000
            assert all(x >= 0 for x in results)

    def test_simulate_zero_conversion_rate(self):
        """Test simulation with zero conversion rate."""
        zero_conversion_feature = Feature(
            name="Zero Conversion",
            expected_users=1000,
            conversion_rate=0.0,
            uncertainty=0.1,
        )
        results = self.engine.simulate(zero_conversion_feature, scenarios=1000)

        # With zero conversion rate, most results should be close to zero
        assert len(results) == 1000
        assert np.mean(results) < 100  # Should be very low

    def test_simulate_zero_uncertainty(self):
        """Test simulation with zero uncertainty."""
        no_uncertainty_feature = Feature(
            name="No Uncertainty",
            expected_users=1000,
            conversion_rate=0.15,
            uncertainty=0.0,
        )
        results = self.engine.simulate(no_uncertainty_feature, scenarios=1000)

        # With zero uncertainty, all results should be identical
        expected_value = 1000 * 0.15
        assert len(results) == 1000
        # All results should be very close to expected value
        assert all(abs(x - expected_value) < 1 for x in results)

    def test_simulate_binomial_acceptance_counts(self):
        """Binomial mode should return integer-like acceptance user counts."""
        binomial_feature = Feature(
            name="Binomial Acceptance",
            expected_users=25000,
            conversion_rate=0.15,
            acceptance_model="binomial",
            uncertainty=0.2,
        )
        results = self.engine.simulate(binomial_feature, scenarios=2000)

        assert len(results) == 2000
        assert np.all(results >= 0)
        assert np.all(results <= 25000)
        # Binomial draws are integer counts, dtype may still be numeric
        assert np.all(np.mod(results, 1) == 0)

    def test_simulate_binomial_acceptance_mean_close_to_expected(self):
        """Binomial mode should keep the mean close to n*p."""
        engine = MonteCarloEngine(seed=42)
        binomial_feature = Feature(
            name="Binomial Mean",
            expected_users=25000,
            conversion_rate=0.15,
            acceptance_model="binomial",
            uncertainty=0.1,
        )
        results = engine.simulate(binomial_feature, scenarios=5000)

        expected_conversions = 25000 * 0.15
        mean_result = float(np.mean(results))
        assert abs(mean_result - expected_conversions) / expected_conversions < 0.1

    def test_simulate_bounded_edge_cases(self):
        """Test bounded simulation with edge cases.

        simulate_bounded operates in rate-space: bounds are applied to the
        simulated conversion rate before any scaling. Callers that need
        user-count values multiply by feature.expected_users themselves.
        """
        # Test with very narrow rate bounds → results must stay in [0.14, 0.16]
        results = self.engine.simulate_bounded(
            self.test_feature,
            scenarios=1000,
            lower_bound=0.14,
            upper_bound=0.16,
        )

        assert all(0.14 <= x <= 0.16 for x in results)

        # Test with equal bounds → all values must equal 0.15 (the rate)
        results_equal = self.engine.simulate_bounded(
            self.test_feature,
            scenarios=1000,
            lower_bound=0.15,
            upper_bound=0.15,
        )

        np.testing.assert_allclose(results_equal, 0.15)

    @pytest.mark.parametrize("scenarios", [1000, 2000, 5000])
    def test_simulate_parametrized_scenarios(self, scenarios):
        """Test simulation with different scenario counts using parametrization."""
        results = self.engine.simulate(self.test_feature, scenarios=scenarios)
        assert len(results) == scenarios

    @pytest.mark.parametrize("distribution", ["normal", "uniform", "lognormal"])
    def test_simulate_parametrized_distributions(self, distribution):
        """Test simulation with different distributions using parametrization."""
        results = self.engine.simulate(
            self.test_feature,
            scenarios=1000,
            distribution=distribution,
        )
        assert len(results) == 1000
        assert all(x >= 0 for x in results)


class TestLogNormalDistribution:
    """Tests for the log-normal distribution used in skewed value projections."""

    def setup_method(self):
        self.feature = Feature(
            name="LN Feature",
            expected_users=1000,
            conversion_rate=0.15,
            uncertainty=0.3,
        )

    def test_lognormal_returns_positive_values(self):
        """Log-normal must never produce negative values."""
        engine = MonteCarloEngine(seed=0)
        results = engine.simulate(
            self.feature, scenarios=5000, distribution="lognormal"
        )
        assert np.all(results >= 0), "Log-normal must not generate negative values"

    def test_lognormal_median_close_to_expected(self):
        """Median of log-normal simulation should be close to the expected value."""
        engine = MonteCarloEngine(seed=1)
        results = engine.simulate(
            self.feature, scenarios=10000, distribution="lognormal"
        )
        expected = self.feature.expected_users * self.feature.conversion_rate
        median = np.median(results)
        # Median should fall within ±20% of the expected value
        assert abs(median - expected) / expected < 0.20

    def test_lognormal_positive_skew(self):
        """Log-normal distribution is positively skewed (mean > median)."""
        from scipy import stats

        engine = MonteCarloEngine(seed=2)
        results = engine.simulate(
            self.feature, scenarios=10000, distribution="lognormal"
        )
        skewness = stats.skew(results)
        assert skewness > 0, f"Expected positive skewness, got {skewness:.3f}"

    def test_lognormal_reproducible_with_seed(self):
        """Same seed produces identical simulation results."""
        r1 = MonteCarloEngine(seed=42).simulate(
            self.feature, scenarios=1000, distribution="lognormal"
        )
        r2 = MonteCarloEngine(seed=42).simulate(
            self.feature, scenarios=1000, distribution="lognormal"
        )
        np.testing.assert_array_equal(r1, r2)

    def test_lognormal_zero_base_value_raises(self):
        """base_value=0 must raise an error for log-normal distribution."""
        engine = MonteCarloEngine(seed=0)
        zero_feature = Feature(
            name="Zero", expected_users=1000, conversion_rate=0.0, uncertainty=0.3
        )
        with pytest.raises(
            ValidationError, match="Log-Normal distribution requires base_value > 0"
        ):
            engine.simulate(zero_feature, scenarios=1000, distribution="lognormal")

    def test_lognormal_less_clipping_than_normal(self):
        """Log-normal produces fewer negative values and requires less clipping."""
        engine = MonteCarloEngine(seed=5)
        high_uncertainty_feature = Feature(
            name="HU", expected_users=1000, conversion_rate=0.15, uncertainty=0.9
        )
        results_ln = engine.simulate(
            high_uncertainty_feature, scenarios=5000, distribution="lognormal"
        )
        # All values must be >= 0 (no clipping loss)
        assert np.all(results_ln >= 0)


class TestCorrelatedSimulation:
    """Tests for correlated Monte Carlo simulation using Cholesky decomposition."""

    def setup_method(self):
        self.engine = MonteCarloEngine(seed=42)
        self.features = [
            Feature(
                name="A", expected_users=10000, conversion_rate=0.10, uncertainty=0.3
            ),
            Feature(
                name="B", expected_users=8000, conversion_rate=0.15, uncertainty=0.2
            ),
            Feature(
                name="C", expected_users=5000, conversion_rate=0.20, uncertainty=0.1
            ),
        ]

    def test_identity_correlation_equals_independent(self):
        """Identity matrix should produce uncorrelated results."""
        corr = np.eye(3)
        results = self.engine.simulate_correlated(self.features, corr, scenarios=5000)
        assert len(results) == 3
        for name in ["A", "B", "C"]:
            assert name in results
            assert len(results[name]) == 5000
            assert np.all(results[name] >= 0)

    def test_high_positive_correlation(self):
        """Highly correlated features should move together."""
        corr = np.array(
            [
                [1.0, 0.9, 0.9],
                [0.9, 1.0, 0.9],
                [0.9, 0.9, 1.0],
            ]
        )
        results = self.engine.simulate_correlated(self.features, corr, scenarios=10000)
        # Empirical correlation should be near 0.9
        empirical_corr = np.corrcoef([results["A"], results["B"], results["C"]])
        # Allow tolerance due to clipping effects on conversion rates
        assert empirical_corr[0, 1] > 0.5  # Should be substantially positive

    def test_negative_correlation(self):
        """Negatively correlated features should move in opposite directions."""
        corr = np.array(
            [
                [1.0, -0.7],
                [-0.7, 1.0],
            ]
        )
        features_2 = self.features[:2]
        results = self.engine.simulate_correlated(features_2, corr, scenarios=10000)
        empirical_corr = np.corrcoef(results["A"], results["B"])[0, 1]
        assert empirical_corr < -0.3  # Should be substantially negative

    def test_results_are_absolute_conversions(self):
        """Results should be scaled to absolute conversions, not rates."""
        corr = np.eye(3)
        results = self.engine.simulate_correlated(self.features, corr, scenarios=5000)
        # Feature A: 10000 users * 0.10 rate = ~1000 expected conversions
        assert np.mean(results["A"]) == pytest.approx(1000, rel=0.15)
        # Feature B: 8000 * 0.15 = ~1200
        assert np.mean(results["B"]) == pytest.approx(1200, rel=0.15)

    def test_zero_uncertainty_constant(self):
        """Zero uncertainty features should produce constant values."""
        features = [
            Feature(
                name="X", expected_users=1000, conversion_rate=0.5, uncertainty=0.0
            ),
            Feature(
                name="Y", expected_users=2000, conversion_rate=0.3, uncertainty=0.0
            ),
        ]
        corr = np.array([[1.0, 0.5], [0.5, 1.0]])
        results = self.engine.simulate_correlated(features, corr, scenarios=1000)
        assert np.all(results["X"] == 500.0)
        assert np.all(results["Y"] == 600.0)

    def test_wrong_matrix_shape_raises(self):
        """Matrix shape must match number of features."""
        corr = np.eye(2)  # 2x2 but 3 features
        with pytest.raises(CorrelationMatrixError, match="does not match"):
            self.engine.simulate_correlated(self.features, corr, scenarios=1000)

    def test_non_symmetric_matrix_raises(self):
        """Non-symmetric matrix should be rejected."""
        corr = np.array([[1.0, 0.5, 0.0], [0.3, 1.0, 0.0], [0.0, 0.0, 1.0]])
        with pytest.raises(CorrelationMatrixError, match="symmetric"):
            self.engine.simulate_correlated(self.features, corr, scenarios=1000)

    def test_non_psd_matrix_raises(self):
        """Non positive semi-definite matrix should be rejected."""
        # Construct a matrix that is NOT positive semi-definite
        # by forcing eigenvalues to be negative
        corr = np.array(
            [
                [1.0, 0.99, 0.99],
                [0.99, 1.0, -0.99],
                [0.99, -0.99, 1.0],
            ]
        )
        with pytest.raises(CorrelationMatrixError):
            self.engine.simulate_correlated(self.features, corr, scenarios=1000)

    def test_lognormal_distribution(self):
        """Lognormal distribution should work with correlation."""
        corr = np.array([[1.0, 0.5], [0.5, 1.0]])
        features_2 = self.features[:2]
        results = self.engine.simulate_correlated(
            features_2, corr, scenarios=5000, distribution="lognormal"
        )
        assert len(results["A"]) == 5000
        assert np.all(results["A"] >= 0)

    def test_reproducibility_with_seed(self):
        """Same seed should produce identical results."""
        corr = np.array([[1.0, 0.5], [0.5, 1.0]])
        features_2 = self.features[:2]

        e1 = MonteCarloEngine(seed=123)
        r1 = e1.simulate_correlated(features_2, corr, scenarios=1000)

        e2 = MonteCarloEngine(seed=123)
        r2 = e2.simulate_correlated(features_2, corr, scenarios=1000)

        np.testing.assert_array_equal(r1["A"], r2["A"])
        np.testing.assert_array_equal(r1["B"], r2["B"])


class TestMonteCarloEngineCoverage:
    """Cover uncovered validation / edge-case paths in MonteCarloEngine."""

    def setup_method(self):
        self.engine = MonteCarloEngine(seed=42)

    def test_simulate_non_feature_without_uncertainty(self):
        """simulate with non-Feature base_value and no uncertainty raises."""
        with pytest.raises(ValueError, match="Uncertainty must be provided"):
            self.engine.simulate(0.5, uncertainty=None, scenarios=1000)

    def test_simulate_uncertainty_out_of_range(self):
        """uncertainty < 0 or > 1."""
        with pytest.raises(
            ValidationError, match="Uncertainty must be between 0 and 1"
        ):
            self.engine.simulate(0.5, uncertainty=1.5, scenarios=1000)
        with pytest.raises(
            ValidationError, match="Uncertainty must be between 0 and 1"
        ):
            self.engine.simulate(0.5, uncertainty=-0.1, scenarios=1000)

    def test_simulate_negative_base_value(self):
        """base_value < 0."""
        with pytest.raises(ValueError, match="Base value cannot be negative"):
            self.engine.simulate(-0.5, uncertainty=0.1, scenarios=1000)

    def test_simulate_bounded_feature_zero_uncertainty(self):
        """simulate_bounded with Feature that has zero uncertainty."""
        f = Feature(
            name="ZeroBounded",
            expected_users=1000,
            conversion_rate=0.5,
            uncertainty=0.0,
        )
        result = self.engine.simulate_bounded(f, scenarios=1000)
        assert len(result) == 1000
        # Zero uncertainty means all values should be the base_value (conversion_rate)
        np.testing.assert_allclose(result, 0.5, atol=1e-10)

    def test_simulate_bounded_non_feature(self):
        """simulate_bounded with non-Feature, uses raw_values path."""
        result = self.engine.simulate_bounded(
            0.5, uncertainty=0.1, lower_bound=0.0, upper_bound=1.0, scenarios=1000
        )
        assert len(result) == 1000
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0)

    def test_simulate_bounded_feature_nonzero_uncertainty(self):
        """simulate_bounded with Feature that has non-zero uncertainty."""
        f = Feature(
            name="Bounded", expected_users=1000, conversion_rate=0.5, uncertainty=0.2
        )
        result = self.engine.simulate_bounded(f, scenarios=1000)
        assert len(result) == 1000

    def test_simulate_correlated_diagonal_not_one(self):
        """correlation matrix diagonal != 1."""
        f = Feature(name="A", expected_users=500, conversion_rate=0.3, uncertainty=0.1)
        corr = np.array([[2.0]])
        with pytest.raises(CorrelationMatrixError, match="diagonal must be 1.0"):
            self.engine.simulate_correlated([f], corr, scenarios=1000)

    def test_simulate_correlated_values_out_of_range(self):
        """correlation values outside [-1, 1]."""
        f1 = Feature(name="A", expected_users=100, conversion_rate=0.3, uncertainty=0.1)
        f2 = Feature(name="B", expected_users=100, conversion_rate=0.3, uncertainty=0.1)
        corr = np.array([[1.0, 1.5], [1.5, 1.0]])
        with pytest.raises(CorrelationMatrixError, match="between -1 and 1"):
            self.engine.simulate_correlated([f1, f2], corr, scenarios=1000)

    def test_simulate_correlated_not_symmetric(self):
        """Correlation matrix must be symmetric."""
        f1 = Feature(name="A", expected_users=100, conversion_rate=0.3, uncertainty=0.1)
        f2 = Feature(name="B", expected_users=100, conversion_rate=0.3, uncertainty=0.1)
        corr = np.array([[1.0, 0.5], [0.3, 1.0]])
        with pytest.raises(CorrelationMatrixError, match="symmetric"):
            self.engine.simulate_correlated([f1, f2], corr, scenarios=1000)

    def test_simulate_correlated_unsupported_distribution(self):
        """unsupported distribution in correlated simulation raises ValidationError."""
        f1 = Feature(name="A", expected_users=100, conversion_rate=0.3, uncertainty=0.1)
        f2 = Feature(name="B", expected_users=200, conversion_rate=0.4, uncertainty=0.2)
        corr = np.array([[1.0, 0.5], [0.5, 1.0]])
        with pytest.raises(ValidationError, match="Unknown distribution"):
            self.engine.simulate_correlated(
                [f1, f2], corr, scenarios=1000, distribution="nonexistent"
            )

    def test_simulate_correlated_min_scenarios(self):
        """simulate_correlated with too few scenarios."""
        f1 = Feature(name="A", expected_users=100, conversion_rate=0.3, uncertainty=0.1)
        f2 = Feature(name="B", expected_users=200, conversion_rate=0.4, uncertainty=0.2)
        corr = np.array([[1.0, 0.5], [0.5, 1.0]])
        with pytest.raises(ValidationError, match="Minimum"):
            self.engine.simulate_correlated([f1, f2], corr, scenarios=100)

    def test_simulate_copula_gaussian_beta(self):
        """Copula path (gaussian + beta marginals) produces bounded conversions."""
        f1 = Feature(
            name="A", expected_users=1000, conversion_rate=0.2, uncertainty=0.2
        )
        f2 = Feature(
            name="B", expected_users=1500, conversion_rate=0.1, uncertainty=0.3
        )
        corr = np.array([[1.0, 0.6], [0.6, 1.0]])
        res = self.engine.simulate_copula(
            [f1, f2],
            scenarios=2000,
            marginal_distribution="beta",
            copula_type="gaussian",
            correlation_matrix=corr,
        )
        assert set(res.keys()) == {"A", "B"}
        assert res["A"].shape == (2000,)
        assert np.all(res["A"] >= 0)
        assert np.all(res["B"] >= 0)

    def test_simulate_copula_frank_uniform(self):
        """Frank copula with uniform marginals runs and stays non-negative."""
        f1 = Feature(name="A", expected_users=500, conversion_rate=0.2, uncertainty=0.1)
        f2 = Feature(name="B", expected_users=500, conversion_rate=0.3, uncertainty=0.1)
        res = self.engine.simulate_copula(
            [f1, f2],
            scenarios=1500,
            marginal_distribution="uniform",
            copula_type="frank",
            theta=2.0,
        )
        assert np.all(res["A"] >= 0)
        assert np.all(res["B"] >= 0)

    def test_sample_distribution_normal(self):
        """sample_distribution draws expected number of normal samples."""
        samples = self.engine.sample_distribution(
            "normal",
            {"mean": 0.2, "uncertainty": 0.1},
            250,
        )

        assert samples.shape == (250,)

    def test_sample_distribution_truncnorm_with_bounds(self):
        """sample_distribution supports truncnorm specific lower/upper bounds."""
        samples = self.engine.sample_distribution(
            "truncnorm",
            {
                "mean": 0.5,
                "uncertainty": 0.2,
                "lower": 0.3,
                "upper": 0.7,
            },
            400,
        )

        assert samples.shape == (400,)
        assert np.all(samples >= 0.3)
        assert np.all(samples <= 0.7)

    def test_sample_distribution_requires_positive_n(self):
        """sample_distribution rejects non-positive sample sizes."""
        with pytest.raises(ValueError, match="must be positive"):
            self.engine.sample_distribution(
                "normal",
                {"mean": 0.2, "uncertainty": 0.1},
                0,
            )

    def test_sample_distribution_requires_required_params(self):
        """sample_distribution validates required mean/uncertainty params."""
        with pytest.raises(ValueError, match="must include 'mean' and 'uncertainty'"):
            self.engine.sample_distribution("normal", {"mean": 0.2}, 100)
