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
Tests for the models module.

This module tests the core data structures used in the Feature Hypotheses Simulation.
"""

import numpy as np
import pytest
from pydantic import ValidationError

from fhs.core.model import Feature, ScenarioConfig, SimulationResult
from fhs.core.model.value_objects import Budget


class TestFeature:
    """Test cases for the Feature class."""

    def test_valid_feature_creation(self):
        """Test creating a valid feature with all required parameters."""
        feature = Feature(
            name="Test Feature",
            expected_users=1000,
            conversion_rate=0.15,
            uncertainty=0.1,
        )

        assert feature.name == "Test Feature"
        assert feature.expected_users == 1000
        assert feature.conversion_rate == 0.15
        assert feature.uncertainty == 0.1

    def test_feature_with_optional_fields(self):
        """Test creating a feature with optional business_value and development_cost."""
        feature = Feature(
            name="Premium",
            expected_users=500,
            conversion_rate=0.2,
            uncertainty=0.1,
            business_value_per_conversion=50.0,
            development_cost=10000.0,
        )

        assert feature.business_value_per_conversion == 50.0
        assert feature.development_cost == 10000.0

    def test_feature_optional_fields_defaults(self):
        """Test that optional fields have correct defaults."""
        feature = Feature(
            name="Defaults",
            expected_users=100,
            conversion_rate=0.1,
            uncertainty=0.05,
        )

        assert feature.business_value_per_conversion == 1.0
        assert feature.development_cost == 0.0
        assert feature.development_weeks is None

    def test_feature_development_weeks_valid(self):
        """Test that development_weeks accepts valid positive integers."""
        feature = Feature(
            name="Timed",
            expected_users=1000,
            conversion_rate=0.1,
            uncertainty=0.2,
            development_weeks=6,
        )
        assert feature.development_weeks == 6

    def test_feature_development_weeks_one(self):
        """Minimum valid value for development_weeks is 1."""
        feature = Feature(
            name="Quick",
            expected_users=500,
            conversion_rate=0.05,
            uncertainty=0.1,
            development_weeks=1,
        )
        assert feature.development_weeks == 1

    @pytest.mark.parametrize("invalid_weeks", [0, -1, -10])
    def test_feature_development_weeks_invalid(self, invalid_weeks):
        """development_weeks must be >= 1; 0 and negatives raise ValidationError."""
        with pytest.raises(ValidationError):
            Feature(
                name="Bad",
                expected_users=1000,
                conversion_rate=0.1,
                uncertainty=0.2,
                development_weeks=invalid_weeks,
            )

    def test_feature_negative_business_value(self):
        """Test that business_value_per_conversion can be negative."""
        feature = Feature(
            name="Costly Feature",
            expected_users=1000,
            conversion_rate=0.1,
            uncertainty=0.1,
            business_value_per_conversion=-10.0,
        )
        assert feature.business_value_per_conversion == -10.0

    def test_simulation_result_net_value_at_risk(self):
        """Test calculation of net_value_at_risk_95 and cvar_95_net_value."""
        results = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        # p5 is between 10 and 20 -> 14.5 (numpy default linear interpolation)
        # var_95 = 14.5
        # threshold = 14.5. tail = [10]. mean(tail) = 10.0
        # cvar_95 = 10.0

        res = SimulationResult(
            feature_name="NetTest",
            results=results,
            expected_value=55.0,
            business_value_per_conversion=2.0,
            development_cost=100.0,
        )

        # var_95 is 14.5 (5th percentile of [10...100])
        # business_value_at_risk_95 = 14.5 * 2.0 = 29.0
        # net_value_at_risk_95 = 29.0 - 100.0 = -71.0
        assert res.var_95 == pytest.approx(14.5)
        assert res.business_value_at_risk_95 == pytest.approx(29.0)
        assert res.net_value_at_risk_95 == pytest.approx(-71.0)

        # cvar_95 is 10.0
        # cvar_95_business_value = 10.0 * 2.0 = 20.0
        # cvar_95_net_value = 20.0 - 100.0 = -80.0
        assert res.cvar_95 == pytest.approx(10.0)
        assert res.cvar_95_net_value == pytest.approx(-80.0)

    def test_business_value_risk_metrics_contains_net_metrics(self):
        """Test that business_value_risk_metrics includes net profit/loss metrics."""
        results = np.array([10, 20, 30, 40, 50])
        res = SimulationResult(
            feature_name="MetricsTest",
            results=results,
            expected_value=30.0,
            business_value_per_conversion=10.0,
            development_cost=500.0,
        )
        metrics = res.business_value_risk_metrics
        assert "minimum_net_value_95" in metrics
        assert "average_worst_case_net_value_95" in metrics
        # var_95 for [10, 20, 30, 40, 50] is 12.0
        # business_value_at_risk_95 = 120.0
        # minimum_net_value_95 = 120.0 - 500.0 = -380.0
        assert metrics["minimum_net_value_95"] == pytest.approx(-380.0)

    @pytest.mark.parametrize(
        "overrides,match",
        [
            ({"expected_users": -100}, "Expected users must be positive"),
            ({"expected_users": 0}, "Expected users must be positive"),
            ({"conversion_rate": -0.1}, "Conversion rate must be between 0 and 1"),
            ({"conversion_rate": 1.5}, "Conversion rate must be between 0 and 1"),
            ({"uncertainty": -0.1}, "Uncertainty must be between 0 and 1"),
            ({"uncertainty": 1.5}, "Uncertainty must be between 0 and 1"),
            ({"name": ""}, "Name must not be empty"),
            ({"name": "   "}, "Name must not be empty"),
        ],
    )
    def test_feature_validation_errors(self, overrides, match):
        """Test that invalid parameters raise ValidationError with correct message."""
        defaults = {
            "name": "Test",
            "expected_users": 1000,
            "conversion_rate": 0.15,
            "uncertainty": 0.1,
        }
        with pytest.raises(ValidationError):
            Feature(**(defaults | overrides))

    def test_feature_boundary_values(self):
        """Test feature creation with boundary values."""
        feature_min = Feature(
            name="Min",
            expected_users=1,
            conversion_rate=0.0,
            uncertainty=0.0,
        )
        assert feature_min.expected_users == 1
        assert feature_min.conversion_rate == 0.0
        assert feature_min.uncertainty == 0.0

        feature_max = Feature(
            name="Max",
            expected_users=1000,
            conversion_rate=1.0,
            uncertainty=1.0,
        )
        assert feature_max.conversion_rate == 1.0
        assert feature_max.uncertainty == 1.0

    @pytest.mark.parametrize(
        "users,rate,uncertainty",
        [
            (100, 0.05, 0.02),
            (5000, 0.25, 0.15),
            (10000, 0.50, 0.30),
            (1, 1.0, 0.0),
        ],
    )
    def test_feature_parametrized_valid_inputs(self, users, rate, uncertainty):
        """Test feature creation with various valid parameter combinations."""
        feature = Feature(
            name="Param Test",
            expected_users=users,
            conversion_rate=rate,
            uncertainty=uncertainty,
        )
        assert feature.expected_users == users
        assert feature.conversion_rate == rate
        assert feature.uncertainty == uncertainty

    def test_feature_str_representation(self):
        """Test __str__ returns a readable representation."""
        feature = Feature(
            name="Login",
            expected_users=500,
            conversion_rate=0.2,
            uncertainty=0.1,
        )
        result = str(feature)
        assert "Login" in result
        assert "500" in result
        assert "0.2" in result
        assert "0.1" in result

    def test_feature_large_expected_users(self):
        """Test that very large expected_users values work without overflow."""
        feature = Feature(
            name="Massive",
            expected_users=10**9,
            conversion_rate=0.01,
            uncertainty=0.5,
        )
        assert feature.expected_users == 10**9

    def test_feature_business_value_zero(self):
        """Test that business_value_per_conversion=0.0 is accepted (boundary)."""
        feature = Feature(
            name="Free",
            expected_users=100,
            conversion_rate=0.5,
            uncertainty=0.1,
            business_value_per_conversion=0.0,
        )
        assert feature.business_value_per_conversion == 0.0


class TestScenarioConfig:
    """Test cases for ScenarioConfig helper views."""

    def test_scenario_budget_value_object(self):
        """ScenarioConfig exposes budget as Budget value object."""
        config = ScenarioConfig(
            scenario_id="demo",
            name="Demo",
            budget=123456.0,
            features=[
                Feature(
                    name="F1",
                    expected_users=1000,
                    conversion_rate=0.2,
                    uncertainty=0.1,
                )
            ],
        )

        assert isinstance(config.budget_value_object, Budget)
        assert config.budget_value_object.amount == pytest.approx(123456.0)

    def test_feature_validators_called_directly(self):
        """Test field validators directly to cover raise
        branches bypassed by Field constraints."""
        with pytest.raises(ValueError, match="empty or whitespace"):
            Feature.name_not_empty("")

        with pytest.raises(ValueError, match="must be positive"):
            Feature.validate_expected_users(0)

        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            Feature.conversion_rate_precision(-0.5)

        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            Feature.uncertainty_precision(2.0)

    def test_feature_from_fixture(self, sample_feature):
        """Test that the shared fixture produces a valid Feature."""
        assert sample_feature.name == "Login"
        assert sample_feature.expected_users == 1000

    def test_scenario_risk_model_defaults(self):
        """ScenarioConfig should expose default risk-model values."""
        config = ScenarioConfig(
            scenario_id="demo",
            name="Demo",
            features=[
                Feature(
                    name="F1",
                    expected_users=1000,
                    conversion_rate=0.2,
                    uncertainty=0.1,
                )
            ],
        )

        assert config.risk_model.risk_2_market_probability == pytest.approx(0.20)
        assert config.risk_model.risk_3_global_probability == pytest.approx(0.05)
        assert config.risk_model.default_component_probability == pytest.approx(0.08)

    def test_scenario_risk_model_cluster_validation(self):
        """Cluster probabilities above 1.0 must fail validation."""
        with pytest.raises(ValidationError):
            ScenarioConfig(
                scenario_id="demo",
                name="Demo",
                risk_model={
                    "component_risk_by_cluster": {
                        "Traceability Platform": 1.2,
                    }
                },
                features=[
                    Feature(
                        name="F1",
                        expected_users=1000,
                        conversion_rate=0.2,
                        uncertainty=0.1,
                    )
                ],
            )


class TestSimulationResult:
    """Test cases for the SimulationResult class."""

    def test_simulation_result_creation(self):
        """Test creating a SimulationResult with valid data."""
        data = [100.0, 150.0, 200.0, 250.0, 300.0]
        sim_result = SimulationResult(
            feature_name="Test Feature",
            results=data,
            var_95=120.0,
            expected_value=200.0,
        )

        assert sim_result.feature_name == "Test Feature"
        assert sim_result.results == data
        assert sim_result.var_95 == 120.0
        assert sim_result.expected_value == 200.0

    def test_simulation_result_properties(self):
        """Test that SimulationResult calculates statistical properties correctly."""
        scenarios = [10.0, 20.0, 30.0, 40.0, 50.0]
        sim_result = SimulationResult(
            feature_name="Test",
            results=scenarios,
            var_95=15.0,
            expected_value=30.0,
        )

        risk_metrics = sim_result.risk_metrics
        assert risk_metrics["expected"] == 30.0
        assert risk_metrics["median"] == 30.0

        percentiles = sim_result.percentiles
        assert percentiles["p50"] == 30.0

    def test_simulation_result_percentiles(self):
        """Test percentile calculations."""
        scenarios = list(range(1, 101))
        sim_result = SimulationResult(
            feature_name="Percentile Test",
            results=scenarios,
            var_95=5.0,
            expected_value=50.0,
        )

        percentiles = sim_result.percentiles
        assert percentiles["p5"] == np.percentile(scenarios, 5)
        assert percentiles["p25"] == np.percentile(scenarios, 25)
        assert percentiles["p75"] == np.percentile(scenarios, 75)
        assert percentiles["p95"] == np.percentile(scenarios, 95)

    def test_simulation_result_empty_metrics_defaults(self):
        """Test default metric values for empty simulation results."""
        sim_result = SimulationResult(feature_name="Empty", results=[])

        assert sim_result.mean == 0.0
        assert sim_result.median == 0.0
        assert sim_result.std == 0.0
        assert sim_result.var_95 == 0.0
        assert sim_result.p5 == 0.0
        assert sim_result.p10 == 0.0
        assert sim_result.p90 == 0.0
        assert sim_result.p95 == 0.0
        assert sim_result.percentiles == {}
        assert sim_result.risk_metrics == {}
        assert sim_result.confidence_interval == [0.0, 0.0]

    def test_simulation_result_empty_business_value_metrics(self):
        """Test that empty results return empty business_value_risk_metrics."""
        sim_result = SimulationResult(feature_name="Empty", results=[])

        assert sim_result.business_value_risk_metrics == {}

    def test_simulation_result_single_value(self):
        """Test SimulationResult with a single value."""
        sim_result = SimulationResult(
            feature_name="Single",
            results=np.array([42]),
            scenarios=1,
        )

        assert sim_result.mean == 42
        assert sim_result.median == 42
        assert sim_result.std == 0
        assert sim_result.p5 == 42
        assert sim_result.p95 == 42

    def test_simulation_result_large_dataset(self):
        """Test SimulationResult with a large dataset."""
        rng = np.random.default_rng(42)
        results = rng.normal(1000, 100, 10000)
        sim_result = SimulationResult(
            feature_name="Large Dataset",
            results=results,
            scenarios=10000,
        )

        assert len(sim_result.results) == 10000
        assert sim_result.scenarios == 10000
        assert 950 < sim_result.mean < 1050
        assert 90 < sim_result.std < 110

    def test_simulation_result_negative_scenarios(self):
        """Test that negative scenarios parameter is stored without validation."""
        sim_result = SimulationResult(
            feature_name="Negative Scenarios",
            results=np.array([1, 2, 3]),
            scenarios=-1,
        )
        assert sim_result.scenarios == -1

    def test_simulation_result_confidence_interval(self):
        """Test confidence interval calculation with known data."""
        scenarios = list(range(1, 101))
        sim_result = SimulationResult(
            feature_name="CI Test",
            results=scenarios,
            expected_value=50.0,
        )

        ci = sim_result.confidence_interval
        assert len(ci) == 2
        assert ci[0] == np.percentile(scenarios, 5)
        assert ci[1] == np.percentile(scenarios, 95)
        assert ci[0] < ci[1]

    def test_simulation_result_var_95_computed(self):
        """Test that var_95 is computed from results when not provided."""
        data = list(range(1, 101))
        sim_result = SimulationResult(
            feature_name="VaR Computed",
            results=data,
            expected_value=50.0,
        )

        expected_var = float(np.percentile(data, 5))
        assert sim_result.var_95 == pytest.approx(expected_var)

    def test_simulation_result_expected_business_value(self):
        """Test expected_business_value = expected_value * business_value_per_conversion."""
        sim_result = SimulationResult(
            feature_name="Business Value Test",
            results=np.array([100, 200, 300]),
            scenarios=3,
            expected_value=200.0,
            business_value_per_conversion=10.0,
        )

        assert sim_result.expected_business_value == 2000.0

    def test_simulation_result_business_value_at_risk_95(self):
        """Test business_value_at_risk_95 = var_95 * business_value_per_conversion."""
        sim_result = SimulationResult(
            feature_name="RaR Test",
            results=np.array([100, 200, 300]),
            scenarios=3,
            expected_value=200.0,
            var_95=120.0,
            business_value_per_conversion=5.0,
        )

        assert sim_result.business_value_at_risk_95 == 600.0

    def test_simulation_result_business_value_risk_metrics(self):
        """Test business_value_risk_metrics scales all metrics by business_value."""
        data = [100.0, 200.0, 300.0, 400.0, 500.0]
        bv = 10.0
        sim_result = SimulationResult(
            feature_name="Business Value Metrics",
            results=data,
            expected_value=300.0,
            var_95=120.0,
            business_value_per_conversion=bv,
        )

        metrics = sim_result.business_value_risk_metrics
        assert metrics["expected_business_value"] == 300.0 * bv
        assert metrics["business_value_at_risk_95"] == 120.0 * bv
        assert "cvar_95_business_value" in metrics
        assert metrics["worst_case_business_value"] == 100.0 * bv
        assert metrics["best_case_business_value"] == 500.0 * bv
        assert metrics["median_business_value"] == 300.0 * bv

    def test_simulation_result_cvar_95(self):
        """Test CVaR 95% is the average of worst 5% scenarios."""
        data = np.arange(1.0, 101.0)  # 1..100
        sim_result = SimulationResult(
            feature_name="CVaR Test",
            results=data,
            expected_value=50.5,
        )
        # VaR 95 = 5th percentile ≈ 5.95
        assert sim_result.cvar_95 <= sim_result.var_95
        assert sim_result.cvar_95 > 0.0

    def test_simulation_result_cvar_95_empty(self):
        """Test CVaR 95% returns 0.0 for empty results."""
        sim_result = SimulationResult(feature_name="Empty CVaR")
        assert sim_result.cvar_95 == 0.0

    def test_simulation_result_cvar_95_single_value(self):
        """Test CVaR 95% with single value falls back to threshold."""
        sim_result = SimulationResult(
            feature_name="Single CVaR",
            results=np.array([42.0]),
            expected_value=42.0,
        )
        assert sim_result.cvar_95 == 42.0

    def test_simulation_result_roi(self):
        """Test ROI = (expected_business_value - development_cost) / development_cost."""
        sim_result = SimulationResult(
            feature_name="ROI Test",
            results=np.array([100]),
            scenarios=1,
            expected_value=200.0,
            business_value_per_conversion=10.0,
            development_cost=1000.0,
        )

        # expected_business_value = 200 * 10 = 2000
        # ROI = (2000 - 1000) / 1000 = 1.0
        assert sim_result.roi == 1.0

    def test_simulation_result_roi_zero_cost(self):
        """Test ROI returns 0.0 when development_cost is zero."""
        sim_result = SimulationResult(
            feature_name="ROI Zero",
            results=np.array([100]),
            scenarios=1,
            expected_value=200.0,
            development_cost=0.0,
        )

        assert sim_result.roi == 0.0

    def test_simulation_result_net_value(self):
        """Test net_value = expected_business_value - development_cost."""
        sim_result = SimulationResult(
            feature_name="Net Value",
            results=np.array([100]),
            scenarios=1,
            expected_value=500.0,
            business_value_per_conversion=2.0,
            development_cost=300.0,
        )

        # expected_business_value = 500 * 2 = 1000
        # net_value = 1000 - 300 = 700
        assert sim_result.net_value == 700.0

    def test_simulation_result_profit_margin(self):
        """Test profit_margin = (business value - cost) / business value."""
        sim_result = SimulationResult(
            feature_name="Margin",
            results=np.array([100]),
            scenarios=1,
            expected_value=400.0,
            business_value_per_conversion=5.0,
            development_cost=1000.0,
        )

        # expected_business_value = 400 * 5 = 2000
        # profit_margin = (2000 - 1000) / 2000 = 0.5
        assert sim_result.profit_margin == 0.5

    def test_simulation_result_profit_margin_zero_business_value(self):
        """Test profit_margin returns 0.0 when expected_business_value is zero."""
        sim_result = SimulationResult(
            feature_name="Margin Zero",
            results=np.array([100]),
            scenarios=1,
            expected_value=0.0,
            development_cost=100.0,
        )

        assert sim_result.profit_margin == 0.0

    def test_simulation_result_invalid_feature_name_empty(self):
        """Test that empty feature_name raises ValidationError."""
        with pytest.raises(ValidationError):
            SimulationResult(feature_name="", results=[1, 2, 3])

    def test_simulation_result_invalid_feature_name_none(self):
        """Test that None feature_name raises ValidationError."""
        with pytest.raises(ValidationError):
            SimulationResult(feature_name=None, results=[1, 2, 3])

    def test_simulation_result_risk_metrics_keys(self):
        """Test that risk_metrics contains all expected keys."""
        sim_result = SimulationResult(
            feature_name="Keys Test",
            results=np.array([10, 20, 30, 40, 50]),
            scenarios=5,
            expected_value=30.0,
            var_95=12.0,
        )

        metrics = sim_result.risk_metrics
        expected_keys = {
            "var_95",
            "cvar_95",
            "expected",
            "worst_case",
            "best_case",
            "std_dev",
            "median",
        }
        assert set(metrics.keys()) == expected_keys
        assert metrics["worst_case"] == 10.0
        assert metrics["best_case"] == 50.0

    def test_simulation_result_business_value_defaults(self):
        """Test default values for
        business_value_per_conversion and development_cost."""
        sim_result = SimulationResult(
            feature_name="Defaults",
            results=np.array([100]),
            scenarios=1,
        )

        assert sim_result.business_value_per_conversion == 1.0
        assert sim_result.development_cost == 0.0

    def test_simulation_result_results_as_plain_list(self):
        """Test that passing results as a plain Python list works correctly."""
        sim_result = SimulationResult(
            feature_name="Plain List",
            results=[10.0, 20.0, 30.0],
            scenarios=3,
        )
        assert sim_result.results == [10.0, 20.0, 30.0]

    def test_simulation_result_results_as_tuple(self):
        """Test that passing results as a tuple is converted to list."""
        sim_result = SimulationResult(
            feature_name="Tuple",
            results=(5.0, 10.0, 15.0),
            scenarios=3,
        )
        assert sim_result.results == [5.0, 10.0, 15.0]

    def test_simulation_result_results_none(self):
        """Test that results=None initializes to empty list."""
        sim_result = SimulationResult(
            feature_name="NoneResults",
            results=None,
            scenarios=0,
        )
        assert sim_result.results == []

    def test_simulation_result_loss_scenario(self):
        """Test financial metrics when development_cost exceeds expected_business_value."""
        sim_result = SimulationResult(
            feature_name="Loss",
            results=np.array([10, 20, 30]),
            scenarios=3,
            expected_value=20.0,
            business_value_per_conversion=5.0,
            development_cost=500.0,
        )

        # expected_business_value = 20 * 5 = 100
        # net_value = 100 - 500 = -400
        # roi = (100 - 500) / 500 = -0.8
        # profit_margin = (100 - 500) / 100 = -4.0
        assert sim_result.net_value == -400.0
        assert sim_result.roi == pytest.approx(-0.8)
        assert sim_result.profit_margin == pytest.approx(-4.0)

    def test_simulation_result_financial_metrics_consistency(self):
        """Test that financial properties are consistent with each other."""
        sim_result = SimulationResult(
            feature_name="Consistency",
            results=np.array([100, 200, 300]),
            scenarios=3,
            expected_value=150.0,
            business_value_per_conversion=8.0,
            development_cost=400.0,
        )

        assert (
            sim_result.expected_business_value
            == sim_result.expected_value * sim_result.business_value_per_conversion
        )
        assert (
            sim_result.net_value
            == sim_result.expected_business_value - sim_result.development_cost
        )
        assert sim_result.roi == pytest.approx(
            (sim_result.expected_business_value - sim_result.development_cost)
            / sim_result.development_cost
        )
        assert sim_result.profit_margin == pytest.approx(
            (sim_result.expected_business_value - sim_result.development_cost)
            / sim_result.expected_business_value
        )
        assert (
            sim_result.business_value_at_risk_95
            == sim_result.var_95 * sim_result.business_value_per_conversion
        )

    def test_simulation_result_from_fixture(self, sample_simulation_result):
        """Test that the shared fixture produces a usable SimulationResult."""
        assert sample_simulation_result.feature_name == "Login"
        assert sample_simulation_result.expected_business_value == 2000.0
        assert sample_simulation_result.development_cost == 500.0

    def test_simulation_result_risk_verdict_thresholds(self):
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

        assert low.risk_verdict()[0] == "LOW RISK"
        assert moderate.risk_verdict()[0] == "MODERATE RISK"
        assert high.risk_verdict()[0] == "HIGH RISK"

    def test_simulation_result_risk_classification_returns_icon(self):
        result = SimulationResult(
            feature_name="Moderate",
            results=np.array([80.0, 120.0]),
            expected_value=100.0,
        )

        label, icon = result.risk_classification()
        assert label == "MODERATE RISK"
        assert icon == "🟡"


class TestFeatureBaseAnnualBusinessValue:
    """Test get_base_annual_business_value() method."""

    def test_get_base_annual_business_value(self):
        """Test deterministic base business value calculation."""
        feature = Feature(
            name="Test",
            expected_users=10_000,
            conversion_rate=0.20,
            uncertainty=0.10,
            business_value_per_conversion=100.0,
        )
        # 10000 * 0.20 * 100 = 200_000
        assert feature.get_base_annual_business_value() == pytest.approx(200_000.0)

    def test_get_base_annual_business_value_default_rpc(self):
        """Test base business value with default business_value_per_conversion=1.0."""
        feature = Feature(
            name="Default RPC",
            expected_users=5_000,
            conversion_rate=0.25,
            uncertainty=0.15,
        )
        # 5000 * 0.25 * 1.0 = 1250
        assert feature.get_base_annual_business_value() == pytest.approx(1_250.0)

    def test_annual_growth_rate_bounds(self):
        """Test that annual_growth_rate accepts valid range."""
        # Valid: -1.0 (complete decline) to 5.0 (500% growth)
        feature = Feature(
            name="High Growth",
            expected_users=1_000,
            conversion_rate=0.10,
            uncertainty=0.30,
            annual_growth_rate=3.0,  # 300% YoY (startup scenario)
        )
        assert feature.annual_growth_rate == 3.0

        # Boundary: -1.0 (complete collapse)
        feature2 = Feature(
            name="Collapse",
            expected_users=1_000,
            conversion_rate=0.10,
            uncertainty=0.30,
            annual_growth_rate=-1.0,
        )
        assert feature2.annual_growth_rate == -1.0

    def test_annual_growth_rate_out_of_bounds(self):
        """Test that annual_growth_rate outside [-1, 5] raises ValidationError."""
        with pytest.raises(ValidationError):
            Feature(
                name="Too High",
                expected_users=1_000,
                conversion_rate=0.10,
                uncertainty=0.10,
                annual_growth_rate=6.0,  # > 5.0
            )

        with pytest.raises(ValidationError):
            Feature(
                name="Too Low",
                expected_users=1_000,
                conversion_rate=0.10,
                uncertainty=0.10,
                annual_growth_rate=-1.5,  # < -1.0
            )


class TestConfigureLogging:
    """Test the configure_logging function."""

    def test_configure_logging_default(self):
        """Test configure_logging uses DEFAULT_CONFIG when called without args."""
        import logging

        from fhs import configure_logging

        logger = configure_logging()
        assert logger.name == "fhs"
        assert logger.level == logging.INFO


class TestInitCoverage:
    """Cover configure_logging with LOG_FILE set."""

    def test_configure_logging_with_log_file(self):
        """configure_logging when LOG_FILE is set."""
        import logging
        import os
        import tempfile

        from fhs import configure_logging
        from fhs.infra.config import SimulationConfig

        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = f.name

        try:
            config = SimulationConfig(LOG_FILE=log_path)
            logger = configure_logging(config)
            assert isinstance(logger, logging.Logger)
            # Verify a file handler was added
            file_handlers = [
                h for h in logger.handlers if isinstance(h, logging.FileHandler)
            ]
            assert len(file_handlers) >= 1
        finally:
            os.unlink(log_path)
            # Cleanup handlers to avoid side effects
            fhs_logger = logging.getLogger("fhs")
            for h in list(fhs_logger.handlers):
                if isinstance(h, logging.FileHandler):
                    h.close()
                    fhs_logger.removeHandler(h)
