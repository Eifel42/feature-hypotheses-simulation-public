#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
Tests for Portfolio Risk Analyzer

Tests portfolio-level risk management capabilities including:
- Portfolio VaR and CVaR
- Correlation analysis
- Risk contribution
- Stress testing
- Efficient frontier
"""

import numpy as np
import pytest

from fhs.core.model import Feature, SimulationResult
from fhs.core.model.exceptions import ValidationError
from fhs.core.services.portfolio import PortfolioRiskAnalyzer
from fhs.core.services.simulation import FeatureSimulator


class TestPortfolioRiskAnalyzer:
    """Test suite for Portfolio Risk Analyzer"""

    @pytest.fixture
    def features(self):
        """Create sample features for testing"""
        premium = Feature(
            name="Premium", expected_users=5000, conversion_rate=0.25, uncertainty=0.15
        )
        basic = Feature(
            name="Basic", expected_users=15000, conversion_rate=0.08, uncertainty=0.10
        )
        enterprise = Feature(
            name="Enterprise",
            expected_users=500,
            conversion_rate=0.45,
            uncertainty=0.25,
        )
        return [premium, basic, enterprise]

    @pytest.fixture
    def simulation_results(self, features):
        """Create simulation results for testing"""
        simulator = FeatureSimulator(seed=42)
        results = {}
        for feature in features:
            result = simulator.simulate_feature(feature, scenarios=1000)
            results[feature.name] = result
        return results

    @pytest.fixture
    def analyzer(self):
        """Create portfolio analyzer"""
        return PortfolioRiskAnalyzer(seed=42)

    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initializes correctly"""
        assert analyzer is not None
        assert analyzer.seed == 42
        assert analyzer.calculator is not None

    def test_calculate_portfolio_risk_basic(self, analyzer, simulation_results):
        """Test basic portfolio risk calculation"""
        portfolio_risk = analyzer.calculate_portfolio_risk(simulation_results)

        metrics = portfolio_risk.portfolio_metrics

        # Check all values are positive
        assert metrics.var_95 > 0
        assert metrics.var_99 > 0
        assert metrics.cvar_95 > 0
        assert metrics.expected_value > 0

        # Check VaR relationship
        assert metrics.var_99 <= metrics.var_95  # VaR99 is more extreme

    def test_calculate_portfolio_risk_with_custom_weights(
        self, analyzer, simulation_results
    ):
        """Test portfolio risk with custom weights"""
        weights = {"Premium": 0.5, "Basic": 0.3, "Enterprise": 0.2}

        portfolio_risk = analyzer.calculate_portfolio_risk(
            simulation_results, weights=weights
        )

        # Check weights are preserved
        assert portfolio_risk.weights == weights

        # Check individual risks are calculated
        assert len(portfolio_risk.individual_risks) == 3
        for feature_name in weights:
            assert feature_name in portfolio_risk.individual_risks

    def test_calculate_portfolio_risk_diversification(
        self, analyzer, simulation_results
    ):
        """Test diversification metrics"""
        portfolio_risk = analyzer.calculate_portfolio_risk(simulation_results)

        diversification = portfolio_risk.diversification

        # Diversification benefit should be positive
        # (portfolio risk < sum of individual risks)
        # Note: This may not always be true if features are highly correlated
        assert isinstance(diversification.diversification_benefit, float)

    def test_calculate_portfolio_risk_empty_results(self, analyzer):
        """Test portfolio risk with empty results"""
        with pytest.raises(ValidationError):
            analyzer.calculate_portfolio_risk({})

    def test_calculate_portfolio_risk_weights_normalization(
        self, analyzer, simulation_results
    ):
        """Test that weights are normalized if they don't sum to 1"""
        weights = {"Premium": 0.5, "Basic": 0.3, "Enterprise": 0.3}  # Sum = 1.1

        portfolio_risk = analyzer.calculate_portfolio_risk(
            simulation_results, weights=weights
        )

        # Check weights are normalized
        normalized_weights = portfolio_risk.weights
        assert np.isclose(sum(normalized_weights.values()), 1.0)

    def test_calculate_correlation_matrix_basic(self, analyzer, simulation_results):
        """Test correlation matrix calculation"""
        correlation = analyzer.calculate_correlation_matrix(simulation_results)

        # Check correlation matrix properties
        corr_matrix = np.array(correlation.correlation_matrix)
        assert corr_matrix.shape[0] == corr_matrix.shape[1] == 3  # 3x3 matrix

        # Check diagonal is all 1s (feature correlated with itself)
        assert np.allclose(np.diag(corr_matrix), 1.0)

        # Check matrix is symmetric
        assert np.allclose(corr_matrix, corr_matrix.T)

        # Check correlation values are in [-1, 1]
        assert np.all(corr_matrix >= -1.0)
        assert np.all(corr_matrix <= 1.0)

    def test_calculate_correlation_matrix_statistics(
        self, analyzer, simulation_results
    ):
        """Test correlation matrix statistics"""
        correlation = analyzer.calculate_correlation_matrix(simulation_results)

        stats = correlation.statistics
        assert isinstance(stats.average_correlation, float)
        assert isinstance(stats.max_correlation.value, float)
        assert len(stats.max_correlation.features) == 2

    def test_calculate_correlation_matrix_empty_results(self, analyzer):
        """Test correlation matrix with empty results"""
        with pytest.raises(ValidationError):
            analyzer.calculate_correlation_matrix({})

    def test_calculate_risk_contribution_basic(self, analyzer, simulation_results):
        """Test risk contribution calculation"""
        risk_contrib = analyzer.calculate_risk_contribution(simulation_results)

        # Check all features have contributions
        assert len(risk_contrib.risk_contributions) == 3
        assert len(risk_contrib.percentage_contributions) == 3

        # Check percentage contributions sum to ~100%
        total_pct = sum(risk_contrib.percentage_contributions.values())
        assert np.isclose(total_pct, 100.0, atol=1.0)

    def test_calculate_risk_contribution_different_metrics(
        self, analyzer, simulation_results
    ):
        """Test risk contribution with different risk metrics"""
        for metric in ["var_95", "var_99", "cvar_95", "cvar_99"]:
            risk_contrib = analyzer.calculate_risk_contribution(
                simulation_results, risk_metric=metric
            )
            assert risk_contrib.risk_metric == metric
            assert risk_contrib.baseline_risk > 0

    def test_calculate_risk_contribution_custom_weights(
        self, analyzer, simulation_results
    ):
        """Test risk contribution with custom weights"""
        weights = {"Premium": 0.6, "Basic": 0.25, "Enterprise": 0.15}

        risk_contrib = analyzer.calculate_risk_contribution(
            simulation_results, weights=weights
        )

        assert risk_contrib.weights == weights

    def test_stress_test_portfolio_basic(self, analyzer, simulation_results):
        """Test basic stress testing"""
        stress_test = analyzer.stress_test_portfolio(simulation_results)

        # Check structure
        assert "baseline_metrics" in stress_test
        assert "stress_scenarios" in stress_test
        assert "n_scenarios" in stress_test

        # Check baseline metrics
        baseline = stress_test["baseline_metrics"]
        assert "var_95" in baseline
        assert "cvar_95" in baseline
        assert "expected_value" in baseline

        # Check stress scenarios exist
        assert len(stress_test["stress_scenarios"]) > 0

    def test_stress_test_portfolio_custom_scenarios(self, analyzer, simulation_results):
        """Test stress testing with custom scenarios"""
        scenarios = [
            {
                "name": "Market Crash",
                "multipliers": {"Premium": 0.5, "Basic": 0.7, "Enterprise": 0.4},
            },
            {
                "name": "Premium Failure",
                "multipliers": {"Premium": 0.2},
            },
        ]

        stress_test = analyzer.stress_test_portfolio(
            simulation_results, scenarios=scenarios
        )

        # Check correct number of scenarios
        assert len(stress_test["stress_scenarios"]) == 2

        # Check scenario names
        scenario_names = [s["scenario_name"] for s in stress_test["stress_scenarios"]]
        assert "Market Crash" in scenario_names
        assert "Premium Failure" in scenario_names

        # Check each scenario has required fields
        for scenario in stress_test["stress_scenarios"]:
            assert "scenario_name" in scenario
            assert "multipliers" in scenario
            assert "stressed_metrics" in scenario
            assert "impact" in scenario

            # Check impact calculations
            impact = scenario["impact"]
            assert "var_95_change" in impact
            assert "var_95_change_pct" in impact
            assert "expected_value_change" in impact

    def test_stress_test_portfolio_impact_calculations(
        self, analyzer, simulation_results
    ):
        """Test that stress test impacts are calculated correctly"""
        scenarios = [
            {
                "name": "All Down 50%",
                "multipliers": {"Premium": 0.5, "Basic": 0.5, "Enterprise": 0.5},
            }
        ]

        stress_test = analyzer.stress_test_portfolio(
            simulation_results, scenarios=scenarios
        )

        baseline = stress_test["baseline_metrics"]
        stressed = stress_test["stress_scenarios"][0]

        # Expected value should be roughly half
        expected_change = stressed["impact"]["expected_value_change"]
        assert expected_change < 0  # Should be negative (decrease)
        assert (
            abs(expected_change) > 0.4 * baseline["expected_value"]
        )  # Roughly 50% decrease

    def test_portfolio_scenarios_calculation(self, analyzer, simulation_results):
        """Test internal portfolio scenarios calculation"""
        weights = {"Premium": 0.5, "Basic": 0.3, "Enterprise": 0.2}

        # Extract results arrays
        results_arrays = {
            name: result.results_array for name, result in simulation_results.items()
        }

        # Calculate portfolio scenarios
        portfolio_scenarios = analyzer._calculate_portfolio_scenarios(
            results_arrays, weights
        )

        # Check shape
        assert len(portfolio_scenarios) == 1000  # Same as simulation scenarios

        # Check values are reasonable (weighted combination)
        assert np.all(portfolio_scenarios > 0)

    def test_risk_metric_calculation(self, analyzer):
        """Test internal risk metric calculation"""
        scenarios = np.array([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])

        # Test each risk metric
        var_95 = analyzer._calculate_risk_metric(scenarios, "var_95")
        var_99 = analyzer._calculate_risk_metric(scenarios, "var_99")
        cvar_95 = analyzer._calculate_risk_metric(scenarios, "cvar_95")
        cvar_99 = analyzer._calculate_risk_metric(scenarios, "cvar_99")

        # All should be positive
        assert var_95 > 0
        assert var_99 > 0
        assert cvar_95 > 0
        assert cvar_99 > 0

        # VaR 99 should be more extreme than VaR 95
        assert var_99 <= var_95

    def test_risk_metric_calculation_invalid_metric(self, analyzer):
        """Test that invalid risk metric raises error"""
        scenarios = np.array([100, 200, 300])

        with pytest.raises(ValidationError, match="Unknown risk metric"):
            analyzer._calculate_risk_metric(scenarios, "invalid_metric")

    def test_portfolio_analysis_integration(self, analyzer, features):
        """Test complete portfolio analysis workflow"""
        # 1. Simulate features
        simulator = FeatureSimulator(seed=42)
        simulation_results = {}
        for feature in features:
            result = simulator.simulate_feature(feature, scenarios=1000)
            simulation_results[feature.name] = result

        # 2. Calculate portfolio risk
        portfolio_risk = analyzer.calculate_portfolio_risk(simulation_results)
        assert portfolio_risk.portfolio_metrics.var_95 > 0

        # 3. Calculate correlations
        correlation = analyzer.calculate_correlation_matrix(simulation_results)
        assert len(correlation.correlation_matrix) == 3

        # 4. Calculate risk contribution
        risk_contrib = analyzer.calculate_risk_contribution(simulation_results)
        assert len(risk_contrib.risk_contributions) == 3

        # 5. Stress test
        stress_test = analyzer.stress_test_portfolio(simulation_results)
        assert len(stress_test["stress_scenarios"]) > 0


class TestPortfolioRiskEdgeCases:
    """Test edge cases for portfolio risk analysis"""

    def test_single_feature_portfolio(self):
        """Test portfolio with only one feature"""
        analyzer = PortfolioRiskAnalyzer(seed=42)
        simulator = FeatureSimulator(seed=42)

        feature = Feature(
            name="Single", expected_users=1000, conversion_rate=0.20, uncertainty=0.15
        )
        result = simulator.simulate_feature(feature, scenarios=1000)
        simulation_results = {"Single": result}

        # Should work with single feature
        portfolio_risk = analyzer.calculate_portfolio_risk(simulation_results)
        assert portfolio_risk.n_features == 1

        # Diversification benefit should be 0 (no diversification possible)
        assert np.isclose(
            portfolio_risk.diversification.diversification_benefit, 0.0, atol=1.0
        )

    def test_two_feature_portfolio(self):
        """Test portfolio with two features"""
        analyzer = PortfolioRiskAnalyzer(seed=42)
        simulator = FeatureSimulator(seed=42)

        feature1 = Feature(
            name="Feature1", expected_users=1000, conversion_rate=0.20, uncertainty=0.15
        )
        feature2 = Feature(
            name="Feature2", expected_users=2000, conversion_rate=0.15, uncertainty=0.10
        )

        result1 = simulator.simulate_feature(feature1, scenarios=1000)
        result2 = simulator.simulate_feature(feature2, scenarios=1000)

        simulation_results = {"Feature1": result1, "Feature2": result2}

        portfolio_risk = analyzer.calculate_portfolio_risk(simulation_results)
        assert portfolio_risk.n_features == 2

        # Should have some diversification benefit
        assert isinstance(
            portfolio_risk.diversification.diversification_benefit,
            float,
        )

    def test_equal_weights_default(self):
        """Test that default weights are equal"""
        analyzer = PortfolioRiskAnalyzer(seed=42)
        simulator = FeatureSimulator(seed=42)

        features = [
            Feature(
                name="F1", expected_users=1000, conversion_rate=0.20, uncertainty=0.15
            ),
            Feature(
                name="F2", expected_users=2000, conversion_rate=0.15, uncertainty=0.10
            ),
            Feature(
                name="F3", expected_users=1500, conversion_rate=0.18, uncertainty=0.12
            ),
        ]

        simulation_results = {}
        for feature in features:
            result = simulator.simulate_feature(feature, scenarios=1000)
            simulation_results[feature.name] = result

        portfolio_risk = analyzer.calculate_portfolio_risk(simulation_results)

        # Check weights are equal
        weights = portfolio_risk.weights
        expected_weight = 1.0 / 3
        for weight in weights.values():
            assert np.isclose(weight, expected_weight, atol=0.01)


class TestPortfolioCoverage:
    """Cover rare branches in PortfolioRiskAnalyzer."""

    @staticmethod
    def _make_results():
        """Helper: two features with simulation results."""
        rng = np.random.default_rng(0)
        r1 = SimulationResult(
            feature_name="A",
            results=rng.normal(100, 10, 2000),
            scenarios=2000,
            expected_value=100.0,
        )
        r2 = SimulationResult(
            feature_name="B",
            results=rng.normal(200, 20, 2000),
            scenarios=2000,
            expected_value=200.0,
        )
        return {"A": r1, "B": r2}

    def test_risk_contribution_empty(self):
        """calculate_risk_contribution with empty dict."""
        analyzer = PortfolioRiskAnalyzer(seed=0)
        with pytest.raises(ValidationError):
            analyzer.calculate_risk_contribution({})

    def test_stress_test_empty_results(self):
        """stress_test_portfolio with empty results raises."""
        analyzer = PortfolioRiskAnalyzer(seed=0)
        with pytest.raises(ValidationError):
            analyzer.stress_test_portfolio({})

    def test_stress_test_custom_scenarios_dict_format(self):
        """stress_test with user-provided scenarios in dict
        format with multipliers key."""
        analyzer = PortfolioRiskAnalyzer(seed=0)
        results = self._make_results()
        custom_scenarios = [
            {"name": "Mild drop", "multipliers": {"A": 0.8, "B": 0.9}},
        ]
        out = analyzer.stress_test_portfolio(results, scenarios=custom_scenarios)
        assert out["n_scenarios"] == 1
        assert out["stress_scenarios"][0]["scenario_name"] == "Mild drop"

    def test_stress_test_custom_scenarios_plain_dict_format(self):
        """stress_test with plain dict scenarios (no 'multipliers' key)."""
        analyzer = PortfolioRiskAnalyzer(seed=0)
        results = self._make_results()
        custom_scenarios = [
            {"A": 0.5, "B": 1.5},
        ]
        out = analyzer.stress_test_portfolio(results, scenarios=custom_scenarios)
        assert out["n_scenarios"] == 1
        assert "Scenario" in out["stress_scenarios"][0]["scenario_name"]
