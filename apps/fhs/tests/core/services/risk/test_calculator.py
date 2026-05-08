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
Tests for the risk_calculator module.

This module tests the financial risk calculation methods
including VaR, CVaR, and other risk metrics.
"""

import numpy as np
import pytest

from fhs.core.model.exceptions import InsufficientDataError, ValidationError
from fhs.core.model.value_objects import ConfidenceLevel, RiskMetric
from fhs.core.services import RiskCalculator


class TestRiskCalculator:
    """Test cases for the RiskCalculator class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.calculator = RiskCalculator()

        # Standard test data - sorted for predictable percentile results
        self.test_data = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])

        # Large dataset for more realistic testing
        rng = np.random.default_rng(42)
        self.large_data = rng.normal(100, 20, 10000)

    def test_calculator_initialization(self):
        """Test that RiskCalculator initializes correctly."""
        calculator = RiskCalculator()
        assert calculator is not None

    def test_calculate_var_basic(self):
        """Test basic VaR calculation."""
        var_5 = self.calculator.calculate_var(self.test_data, confidence_level=0.95)

        # For our test data [10,20,30,40,50,60,70,80,90,100]
        # 5th percentile should be 14.5 (interpolated between 10 and 20)
        expected_var = np.percentile(self.test_data, 5)
        assert abs(var_5 - expected_var) < 0.1

    def test_calculate_var_invalid_confidence_level(self):
        """Test that invalid confidence levels raise ValidationError."""
        with pytest.raises(
            ValidationError, match="Confidence level must be between 0 and 1"
        ):
            self.calculator.calculate_var(self.test_data, confidence_level=1.5)

        with pytest.raises(
            ValidationError, match="Confidence level must be between 0 and 1"
        ):
            self.calculator.calculate_var(self.test_data, confidence_level=-0.1)

    def test_calculate_cvar_basic(self):
        """Test basic CVaR (Conditional VaR) calculation."""
        cvar_5 = self.calculator.calculate_cvar(self.test_data, confidence_level=0.95)

        # CVaR should be the mean of values below the VaR threshold
        var_5 = self.calculator.calculate_var(self.test_data, 0.95)
        tail_values = self.test_data[self.test_data <= var_5]
        expected_cvar = np.mean(tail_values) if len(tail_values) > 0 else var_5

        assert abs(cvar_5 - expected_cvar) < 0.1

    def test_calculate_cvar_invalid_confidence_level(self):
        """Test that CVaR calculation validates confidence levels."""
        with pytest.raises(
            ValidationError, match="Confidence level must be between 0 and 1"
        ):
            self.calculator.calculate_cvar(self.test_data, confidence_level=2.0)

    def test_calculate_percentile_basic(self):
        """Test percentile calculation."""
        p50 = self.calculator.calculate_percentile(self.test_data, 50)
        assert p50 == np.percentile(self.test_data, 50)

    def test_calculate_percentile_edge_cases(self):
        """Test percentile calculation with edge cases."""
        # Test 0th and 100th percentiles
        p0 = self.calculator.calculate_percentile(self.test_data, 0)
        p100 = self.calculator.calculate_percentile(self.test_data, 100)

        assert p0 == np.min(self.test_data)
        assert p100 == np.max(self.test_data)

    def test_calculate_percentile_invalid_values(self):
        """Test that invalid percentile values raise ValidationError."""
        with pytest.raises(
            ValidationError, match="Percentile must be between 0 and 100"
        ):
            self.calculator.calculate_percentile(self.test_data, -1)

        with pytest.raises(
            ValidationError, match="Percentile must be between 0 and 100"
        ):
            self.calculator.calculate_percentile(self.test_data, 101)

    def test_bootstrap_confidence_interval_basic(self):
        """Test bootstrap confidence interval calculation."""
        ci_lower, ci_upper = self.calculator.bootstrap_confidence_interval(
            self.test_data, confidence_level=0.95, n_bootstrap=1000
        )

        # Basic sanity checks
        assert ci_lower <= ci_upper
        assert isinstance(ci_lower, float | np.floating)
        assert isinstance(ci_upper, float | np.floating)

    def test_bootstrap_confidence_interval_invalid_inputs(self):
        """Test bootstrap CI calculation with invalid inputs."""
        with pytest.raises(
            ValidationError, match="Confidence level must be between 0 and 1"
        ):
            self.calculator.bootstrap_confidence_interval(
                self.test_data, confidence_level=1.5
            )

        with pytest.raises(
            ValidationError, match="Number of bootstrap samples must be positive"
        ):
            self.calculator.bootstrap_confidence_interval(
                self.test_data, n_bootstrap=-100
            )

    def test_bootstrap_confidence_interval_reproducibility(self):
        """Test that bootstrap CI is reproducible with the same rng seed."""
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        ci1_lower, ci1_upper = self.calculator.bootstrap_confidence_interval(
            self.test_data, n_bootstrap=1000, rng=rng1
        )
        ci2_lower, ci2_upper = self.calculator.bootstrap_confidence_interval(
            self.test_data, n_bootstrap=1000, rng=rng2
        )

        assert abs(ci1_lower - ci2_lower) < 1e-10
        assert abs(ci1_upper - ci2_upper) < 1e-10

    def test_empty_data_handling(self):
        """Test handling of empty data arrays."""
        empty_data = np.array([])

        # These should handle empty arrays gracefully or raise appropriate errors
        with pytest.raises((ValueError, IndexError)):
            self.calculator.calculate_var(empty_data)

        with pytest.raises((ValueError, IndexError)):
            self.calculator.calculate_cvar(empty_data)

    def test_single_value_data(self):
        """Test calculations with single-value datasets."""
        single_data = np.array([42])

        var = self.calculator.calculate_var(single_data)
        cvar = self.calculator.calculate_cvar(single_data)
        p50 = self.calculator.calculate_percentile(single_data, 50)

        # All should return the single value
        assert var == 42
        assert cvar == 42
        assert p50 == 42

    def test_large_dataset_performance(self):
        """Test calculations with large datasets for performance."""
        var = self.calculator.calculate_var(self.large_data)
        cvar = self.calculator.calculate_cvar(self.large_data)

        # Basic sanity checks for large dataset
        assert isinstance(var, float | np.floating)
        assert isinstance(cvar, float | np.floating)
        assert cvar <= var  # CVaR should be more conservative (lower) than VaR

    def test_var_cvar_relationship(self):
        """Test the mathematical relationship between VaR and CVaR."""
        var_95 = self.calculator.calculate_var(self.test_data, 0.95)
        cvar_95 = self.calculator.calculate_cvar(self.test_data, 0.95)

        # CVaR should be less than or equal to VaR (more conservative)
        assert cvar_95 <= var_95

    @pytest.mark.parametrize("confidence_level", [0.90, 0.95, 0.99])
    def test_var_parametrized_confidence_levels(self, confidence_level):
        """Test VaR calculation with various confidence levels."""
        var = self.calculator.calculate_var(self.test_data, confidence_level)

        # VaR should be a valid number
        assert isinstance(var, float | np.floating)
        assert not np.isnan(var)
        assert not np.isinf(var)

        # Verify computed value matches expected percentile
        percentile = (1 - confidence_level) * 100
        expected = np.percentile(self.test_data, percentile)
        assert abs(var - expected) < 0.1

    @pytest.mark.parametrize("percentile", [5, 25, 50, 75, 95])
    def test_percentile_parametrized(self, percentile):
        """Test percentile calculation with various percentile values."""
        result = self.calculator.calculate_percentile(self.test_data, percentile)
        expected = np.percentile(self.test_data, percentile)

        assert abs(result - expected) < 1e-10

    def test_negative_values_handling(self):
        """Test handling of datasets with negative values."""
        negative_data = np.array([-50, -30, -10, 0, 10, 30, 50])

        var = self.calculator.calculate_var(negative_data)
        cvar = self.calculator.calculate_cvar(negative_data)

        # Should handle negative values correctly
        assert isinstance(var, float | np.floating)
        assert isinstance(cvar, float | np.floating)

    def test_identical_values_dataset(self):
        """Test calculations with dataset containing identical values."""
        identical_data = np.array([100, 100, 100, 100, 100])

        var = self.calculator.calculate_var(identical_data)
        cvar = self.calculator.calculate_cvar(identical_data)
        p50 = self.calculator.calculate_percentile(identical_data, 50)

        # All should return the same value
        assert var == 100
        assert cvar == 100
        assert p50 == 100

    def test_calculate_risk_metric_returns_value_object(self):
        """calculate_risk_metric returns typed RiskMetric value object."""
        metric = self.calculator.calculate_risk_metric(
            self.test_data, ConfidenceLevel(level=0.95)
        )

        assert isinstance(metric, RiskMetric)
        assert metric.confidence_level == pytest.approx(0.95)
        assert metric.cvar <= metric.var

    def test_extreme_values_dataset(self):
        """Test calculations with dataset containing extreme values."""
        extreme_data = np.array([1, 2, 3, 4, 1000000])  # One extreme outlier

        var_95 = self.calculator.calculate_var(extreme_data, 0.95)
        cvar_95 = self.calculator.calculate_cvar(extreme_data, 0.95)

        # Should handle extreme values without crashing
        assert isinstance(var_95, float | np.floating)
        assert isinstance(cvar_95, float | np.floating)
        assert not np.isnan(var_95)
        assert not np.isnan(cvar_95)


class TestRiskCalculatorCoverage:
    """Cover calculate_risk_metrics static method."""

    def test_calculate_risk_metrics_normal(self):
        """Full calculate_risk_metrics path with valid data."""
        rng = np.random.default_rng(42)
        data = rng.normal(100, 20, 5000)
        metrics = RiskCalculator.calculate_risk_metrics(data)

        assert "expected" in metrics
        assert "var_95" in metrics
        assert "skewness" in metrics
        assert "kurtosis" in metrics
        assert "min" in metrics
        assert "max" in metrics
        assert "median" in metrics
        assert metrics["std_dev"] > 0

    def test_calculate_risk_metrics_with_nans(self):
        """NaN values are cleaned before calculation."""
        data = np.array([1.0, 2.0, np.nan, 4.0, 5.0, np.nan, 7.0])
        metrics = RiskCalculator.calculate_risk_metrics(data)
        assert metrics["expected"] == pytest.approx(np.mean([1, 2, 4, 5, 7]))

    def test_calculate_risk_metrics_all_nan(self):
        """All-NaN array raises InsufficientDataError."""
        data = np.array([np.nan, np.nan])
        with pytest.raises(InsufficientDataError, match="No valid scenarios"):
            RiskCalculator.calculate_risk_metrics(data)

    def test_calculate_risk_metrics_zero_std(self):
        """Zero std_dev sets skewness and kurtosis to 0."""
        data = np.array([42.0, 42.0, 42.0, 42.0])
        metrics = RiskCalculator.calculate_risk_metrics(data)
        assert metrics["skewness"] == 0.0
        assert metrics["kurtosis"] == 0.0
        assert metrics["std_dev"] == 0.0
