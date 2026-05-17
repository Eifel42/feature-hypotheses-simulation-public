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
Tests for the simulator module.

This module tests the main FeatureSimulator orchestration class.
"""

from unittest.mock import patch

import numpy as np
import pytest

from fhs.core.model import Feature, SimulationResult
from fhs.core.model.exceptions import SimulationError, ValidationError
from fhs.core.services import FeatureSimulator
from fhs.core.services.financial import FinancialCalculator
from fhs.plotting.simulation import plot_comparison, plot_results


class TestFeatureSimulator:
    """Test cases for the FeatureSimulator class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.simulator = FeatureSimulator()
        self.test_feature = Feature(
            name="Test Feature",
            expected_users=1000,
            conversion_rate=0.15,
            uncertainty=0.1,
        )

    def test_simulator_initialization(self):
        """Test that FeatureSimulator initializes correctly."""
        simulator = FeatureSimulator()
        assert simulator is not None

        # Test with custom seed
        simulator_with_seed = FeatureSimulator(seed=42)
        assert simulator_with_seed is not None

    def test_classify_risk_thresholds(self):
        low = SimulationResult(
            feature_name="Low",
            results=np.array([100.0, 100.0, 100.0]),
            expected_value=100.0,
        )
        moderate = SimulationResult(
            feature_name="Moderate",
            results=np.array([80.0, 120.0]),
            expected_value=100.0,
        )
        high = SimulationResult(
            feature_name="High",
            results=np.array([0.0, 200.0]),
            expected_value=100.0,
        )

        assert FeatureSimulator.classify_risk(low)[0] == "LOW RISK"
        assert FeatureSimulator.classify_risk(moderate)[0] == "MODERATE RISK"
        assert FeatureSimulator.classify_risk(high)[0] == "HIGH RISK"

    def test_simulate_feature_basic(self):
        """Test basic feature simulation."""
        result = self.simulator.simulate_feature(self.test_feature, scenarios=1000)

        assert isinstance(result, SimulationResult)
        assert result.feature_name == "Test Feature"
        assert result.scenarios == 1000
        assert len(result.results) == 1000

    def test_simulate_feature_minimum_scenarios(self):
        """Test that minimum scenarios requirement is enforced."""
        with pytest.raises(ValidationError, match="Minimum 1000 scenarios required"):
            self.simulator.simulate_feature(self.test_feature, scenarios=500)

    def test_simulate_feature_statistical_properties(self):
        """Test that simulation results have expected statistical properties."""
        simulator = FeatureSimulator(seed=42)
        result = simulator.simulate_feature(self.test_feature, scenarios=5000)

        # Expected value should be close to expected_users * conversion_rate
        expected_value = (
            self.test_feature.expected_users * self.test_feature.conversion_rate
        )

        # Allow for some variance due to uncertainty and randomness
        assert abs(result.mean - expected_value) < expected_value * 0.3
        assert result.std > 0  # Should have some variability

    def test_analyze_risk_basic(self):
        """Test basic risk analysis functionality."""
        result = self.simulator.simulate_feature(self.test_feature, scenarios=1000)
        risk_analysis = self.simulator.analyze_risk(result)

        # Check that risk analysis returns expected keys
        expected_keys = [
            "var_95",
            "var_99",
            "cvar_95",
            "cvar_99",
            "confidence_interval",
        ]
        for key in expected_keys:
            assert key in risk_analysis

        # Check that values are reasonable
        assert isinstance(risk_analysis["var_95"], float | np.floating)
        assert isinstance(risk_analysis["var_99"], float | np.floating)
        assert isinstance(risk_analysis["cvar_95"], float | np.floating)
        assert isinstance(risk_analysis["cvar_99"], float | np.floating)
        assert len(risk_analysis["confidence_interval"]) == 2

    def test_analyze_risk_mathematical_relationships(self):
        """Test mathematical relationships in risk analysis."""
        result = self.simulator.simulate_feature(self.test_feature, scenarios=1000)
        risk_analysis = self.simulator.analyze_risk(result)

        # VaR 99% should be more conservative (lower) than VaR 95%
        assert risk_analysis["var_99"] <= risk_analysis["var_95"]

        # CVaR should be more conservative than VaR
        assert risk_analysis["cvar_95"] <= risk_analysis["var_95"]
        assert risk_analysis["cvar_99"] <= risk_analysis["var_99"]

    def test_compare_features_basic(self):
        """Test basic feature comparison functionality."""
        feature1 = Feature(
            name="Feature A", expected_users=1000, conversion_rate=0.15, uncertainty=0.1
        )
        feature2 = Feature(
            name="Feature B", expected_users=1000, conversion_rate=0.25, uncertainty=0.1
        )

        comparison = self.simulator.compare_features(
            [feature1, feature2], scenarios=1000
        )

        # Should return comparison data for both features
        assert len(comparison) == 2
        for feature_name in ["Feature A", "Feature B"]:
            assert feature_name in comparison
            assert "simulation_result" in comparison[feature_name]
            assert "risk_analysis" in comparison[feature_name]

    def test_compare_features_single_feature(self):
        """Test feature comparison with single feature."""
        comparison = self.simulator.compare_features(
            [self.test_feature], scenarios=1000
        )

        assert len(comparison) == 1
        assert "Test Feature" in comparison

    def test_compare_features_empty_list(self):
        """Test feature comparison with empty feature list."""
        comparison = self.simulator.compare_features([], scenarios=1000)

        assert len(comparison) == 0
        assert isinstance(comparison, dict)

    def test_compare_features_risk_ranking(self):
        """Test that feature comparison provides meaningful risk ranking."""
        # Create features with different risk profiles
        low_risk = Feature(
            name="Low Risk", expected_users=1000, conversion_rate=0.15, uncertainty=0.01
        )  # Low uncertainty
        high_risk = Feature(
            name="High Risk", expected_users=1000, conversion_rate=0.15, uncertainty=0.3
        )  # High uncertainty

        comparison = self.simulator.compare_features(
            [low_risk, high_risk], scenarios=1000
        )

        low_risk_var = comparison["Low Risk"]["risk_analysis"]["var_95"]
        high_risk_var = comparison["High Risk"]["risk_analysis"]["var_95"]

        # High risk feature should have lower VaR (more conservative)
        assert high_risk_var < low_risk_var

    @patch("matplotlib.pyplot.show")
    def test_plot_results_basic(self, mock_show):
        """Test basic results plotting functionality."""
        result = self.simulator.simulate_feature(self.test_feature, scenarios=1000)

        # Should not raise an exception
        plot_results(result)

        # Verify that matplotlib was called
        mock_show.assert_called_once()

    @patch("matplotlib.pyplot.show")
    def test_plot_results_with_risk_analysis(self, mock_show):
        """Test plotting results with risk analysis."""
        result = self.simulator.simulate_feature(self.test_feature, scenarios=1000)
        risk_analysis = self.simulator.analyze_risk(result)

        # Should not raise an exception
        plot_results(result, risk_analysis)

        mock_show.assert_called_once()

    @patch("matplotlib.pyplot.show")
    def test_plot_results_with_empty_data(self, mock_show):
        """Test plotting with empty results returns early."""
        empty_result = SimulationResult(feature_name="Empty", results=[], scenarios=0)

        plot_results(empty_result)

        mock_show.assert_not_called()

    @patch("matplotlib.pyplot.show")
    def test_plot_comparison_basic(self, mock_show):
        """Test basic comparison plotting."""
        feature1 = Feature(
            name="Feature A", expected_users=1000, conversion_rate=0.15, uncertainty=0.1
        )
        feature2 = Feature(
            name="Feature B", expected_users=1000, conversion_rate=0.25, uncertainty=0.1
        )

        comparison = self.simulator.compare_features(
            [feature1, feature2], scenarios=1000
        )

        # Should not raise an exception
        plot_comparison(comparison)

        mock_show.assert_called_once()

    def test_multiple_features_simulation(self):
        """Test simulation of multiple different features."""
        features = [
            Feature(
                name="Low Conversion",
                expected_users=1000,
                conversion_rate=0.05,
                uncertainty=0.02,
            ),
            Feature(
                name="Medium Conversion",
                expected_users=1000,
                conversion_rate=0.15,
                uncertainty=0.1,
            ),
            Feature(
                name="High Conversion",
                expected_users=1000,
                conversion_rate=0.30,
                uncertainty=0.15,
            ),
        ]

        results = []
        for feature in features:
            result = self.simulator.simulate_feature(feature, scenarios=1000)
            results.append(result)
            assert isinstance(result, SimulationResult)
            assert result.feature_name == feature.name

    def test_simulation_with_extreme_parameters(self):
        """Test simulation with extreme feature parameters."""
        # Feature with very high uncertainty
        extreme_feature = Feature(
            name="Extreme", expected_users=1000, conversion_rate=0.15, uncertainty=0.5
        )
        result = self.simulator.simulate_feature(extreme_feature, scenarios=1000)

        assert isinstance(result, SimulationResult)
        assert result.std > 0  # Should have high variability

    def test_zero_uncertainty_feature(self):
        """Test simulation with zero uncertainty feature."""
        zero_uncertainty = Feature(
            name="No Uncertainty",
            expected_users=1000,
            conversion_rate=0.15,
            uncertainty=0.0,
        )
        result = self.simulator.simulate_feature(zero_uncertainty, scenarios=1000)

        # With zero uncertainty, results should be very consistent
        assert result.std < 10  # Should have very low variability

    def test_analyze_risk_edge_cases(self):
        """Test risk analysis with edge case simulation results."""
        # Create a result with very consistent values
        consistent_results = np.full(1000, 150)  # All values are 150
        consistent_sim_result = SimulationResult("Consistent", consistent_results, 1000)

        risk_analysis = self.simulator.analyze_risk(consistent_sim_result)

        # All risk metrics should be similar when there's no variance
        assert abs(risk_analysis["var_95"] - 150) < 1
        assert abs(risk_analysis["cvar_95"] - 150) < 1

    @pytest.mark.parametrize("scenarios", [1000, 2000, 5000])
    def test_simulate_feature_parametrized_scenarios(self, scenarios):
        """Test feature simulation with different scenario counts."""
        result = self.simulator.simulate_feature(self.test_feature, scenarios=scenarios)
        assert len(result.results) == scenarios
        assert result.scenarios == scenarios

    @pytest.mark.parametrize("distribution", ["normal", "uniform", "lognormal"])
    def test_simulate_feature_parametrized_distributions(self, distribution):
        """Test feature simulation with different distributions."""
        result = self.simulator.simulate_feature(
            self.test_feature,
            scenarios=1000,
            distribution=distribution,
        )
        assert len(result.results) == 1000

    def test_memory_efficiency_large_simulation(self):
        """Test memory efficiency with large simulations."""
        # This test ensures we don't have memory leaks with large datasets
        result = self.simulator.simulate_feature(self.test_feature, scenarios=10000)

        # Basic validation
        assert len(result.results) == 10000
        assert isinstance(result.mean, float | np.floating)

        # Ensure results are reasonable
        assert not np.any(np.isnan(result.results))
        assert not np.any(np.isinf(result.results))


class TestRngPropagation:
    """
    Integration tests: Verify that a given seed propagates through the full
    simulation pipeline (FeatureSimulator → MonteCarloEngine → RiskCalculator bootstrap)
    in an isolated and reproducible manner.
    """

    def setup_method(self):
        self.feature = Feature(
            name="Propagation Feature",
            expected_users=500,
            conversion_rate=0.20,
            uncertainty=0.15,
        )

    def test_same_seed_same_results(self):
        """Same seed produces bit-identical simulation results."""
        s1 = FeatureSimulator(seed=99)
        s2 = FeatureSimulator(seed=99)
        r1 = s1.simulate_feature(self.feature, scenarios=2000)
        r2 = s2.simulate_feature(self.feature, scenarios=2000)
        np.testing.assert_array_equal(r1.results, r2.results)

    def test_different_seed_different_results(self):
        """Different seeds produce different outcomes."""
        r1 = FeatureSimulator(seed=1).simulate_feature(self.feature, scenarios=2000)
        r2 = FeatureSimulator(seed=2).simulate_feature(self.feature, scenarios=2000)
        assert not np.array_equal(r1.results, r2.results)

    def test_no_global_state_pollution(self):
        """Two independent simulators do not pollute each other's state."""
        s_seeded = FeatureSimulator(seed=7)
        s_unseeded = FeatureSimulator()  # independent RNG instance

        # Many draws from the global state via s_unseeded
        for _ in range(5):
            s_unseeded.simulate_feature(self.feature, scenarios=1000)

        # s_seeded must still be reproducible
        r_before = FeatureSimulator(seed=7).simulate_feature(
            self.feature, scenarios=1000
        )
        r_after = s_seeded.simulate_feature(self.feature, scenarios=1000)
        np.testing.assert_array_equal(r_before.results, r_after.results)

    def test_bootstrap_reproducible_via_seed(self):
        """Bootstrap confidence interval is reproducible
        when simulator is initialized with a seed."""
        result = FeatureSimulator(seed=42).simulate_feature(
            self.feature, scenarios=2000
        )
        risk1 = FeatureSimulator(seed=42).analyze_risk(result)
        risk2 = FeatureSimulator(seed=42).analyze_risk(result)
        assert risk1["confidence_interval"] == risk2["confidence_interval"]


class TestMultiYearSimulation:
    """Tests for simulate_feature_multi_year()."""

    def setup_method(self):
        self.feature = Feature(
            name="Growth Feature",
            expected_users=10_000,
            conversion_rate=0.20,
            uncertainty=0.25,
            business_value_per_conversion=100.0,
            annual_growth_rate=0.20,
        )

    def test_returns_multi_year_result(self):
        result = FeatureSimulator(seed=42).simulate_feature_multi_year(
            self.feature, scenarios=2_000
        )

        assert result.feature_name == "Growth Feature"
        assert len(result.years) == 3

    def test_each_year_has_correct_shape(self):
        result = FeatureSimulator(seed=42).simulate_feature_multi_year(
            self.feature, scenarios=1_500
        )

        for year in result.years:
            assert len(year.scenarios) == 1_500

    def test_growth_compounding_in_expected_values(self):
        result = FeatureSimulator(seed=42).simulate_feature_multi_year(
            self.feature, scenarios=20_000
        )

        assert result.years[1].expected == pytest.approx(
            result.years[0].expected * 1.20,
            rel=0.08,
        )
        assert result.years[2].expected == pytest.approx(
            result.years[1].expected * 1.20,
            rel=0.08,
        )

    def test_zero_growth_keeps_expected_values_flat(self):
        feature = self.feature.model_copy(update={"annual_growth_rate": 0.0})
        result = FeatureSimulator(seed=42).simulate_feature_multi_year(
            feature, scenarios=20_000
        )

        assert result.years[1].expected == pytest.approx(
            result.years[0].expected, rel=0.06
        )
        assert result.years[2].expected == pytest.approx(
            result.years[0].expected, rel=0.06
        )

    def test_negative_growth_reduces_expected_values(self):
        feature = self.feature.model_copy(update={"annual_growth_rate": -0.10})
        result = FeatureSimulator(seed=42).simulate_feature_multi_year(
            feature, scenarios=20_000
        )

        assert result.years[1].expected < result.years[0].expected
        assert result.years[2].expected < result.years[1].expected

    def test_zero_uncertainty_produces_constant_draws(self):
        feature = self.feature.model_copy(update={"uncertainty": 0.0})
        result = FeatureSimulator(seed=42).simulate_feature_multi_year(
            feature, scenarios=1_000
        )

        for year in result.years:
            assert np.std(year.scenarios) == pytest.approx(0.0)

    def test_reproducible_with_seed(self):
        sim1 = FeatureSimulator(seed=42)
        sim2 = FeatureSimulator(seed=42)
        result1 = sim1.simulate_feature_multi_year(self.feature, scenarios=2_000)
        result2 = sim2.simulate_feature_multi_year(self.feature, scenarios=2_000)

        for year1, year2 in zip(result1.years, result2.years, strict=False):
            np.testing.assert_array_equal(year1.scenarios, year2.scenarios)

    def test_discount_rate_affects_npv(self):
        fc = FinancialCalculator
        sim = FeatureSimulator(seed=42)
        low_discount = sim.simulate_feature_multi_year(
            self.feature, scenarios=2_000, discount_rate=0.05
        )
        high_discount = sim.simulate_feature_multi_year(
            self.feature, scenarios=2_000, discount_rate=0.20
        )

        assert fc.result_npv_expected(low_discount) > fc.result_npv_expected(
            high_discount
        )

    def test_total_3y_expected_is_sum_of_years(self):
        fc = FinancialCalculator
        result = FeatureSimulator(seed=42).simulate_feature_multi_year(
            self.feature, scenarios=2_000
        )

        assert fc.result_total_3y_expected(result) == pytest.approx(
            sum(year.expected for year in result.years)
        )

    def test_total_3y_and_npv_percentiles_are_ordered(self):
        fc = FinancialCalculator
        result = FeatureSimulator(seed=42).simulate_feature_multi_year(
            self.feature, scenarios=2_000
        )

        assert (
            fc.result_total_3y_var_95(result)
            <= fc.result_total_3y_expected(result)
            <= fc.result_total_3y_p95(result)
        )
        assert (
            fc.result_npv_var_95(result)
            <= fc.result_npv_expected(result)
            <= fc.result_npv_p95(result)
        )

    def test_lognormal_end_to_end(self):
        """Log-normal end-to-end through the full simulator
        stack: values >= 0, median close to expected value."""
        sim = FeatureSimulator(seed=0)
        result = sim.simulate_feature(
            self.feature, scenarios=5000, distribution="lognormal"
        )

        results_arr = np.array(result.results)
        assert np.all(results_arr >= 0)

        expected = self.feature.expected_users * self.feature.conversion_rate
        median = np.median(results_arr)
        assert abs(median - expected) / expected < 0.25


class TestSimulatorCoverage:
    """Cover exception-handling paths in FeatureSimulator."""

    def test_simulate_feature_generic_exception_wraps_simulation_error(self):
        """Generic Exception caught and wrapped in SimulationError."""
        sim = FeatureSimulator(seed=None)
        feature = Feature(
            name="X", expected_users=100, conversion_rate=0.3, uncertainty=0.1
        )

        with (
            patch.object(
                sim.engine, "simulate", side_effect=RuntimeError("internal error")
            ),
            pytest.raises(SimulationError, match="Simulation failed"),
        ):
            sim.simulate_feature(feature, scenarios=1000)

    def test_analyze_risk_empty_results(self):
        """analyze_risk with empty results raises SimulationError."""
        sim = FeatureSimulator()
        empty = SimulationResult(feature_name="Empty", results=[], scenarios=0)
        with pytest.raises(SimulationError, match="No simulation results"):
            sim.analyze_risk(empty)

    def test_analyze_risk_generic_exception_wraps_simulation_error(self):
        """Generic Exception in analyze_risk wrapped in SimulationError."""
        sim = FeatureSimulator()
        result = SimulationResult(
            feature_name="T",
            results=np.array([1.0, 2.0, 3.0]),
            scenarios=3,
        )
        with (
            patch.object(
                sim.calculator, "calculate_var", side_effect=RuntimeError("calc boom")
            ),
            pytest.raises(SimulationError, match="Risk analysis failed"),
        ):
            sim.analyze_risk(result)
