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
Tests for Portfolio Optimizer (Exact, Hybrid, ILP Solvers + Delivery Risk)
"""

import numpy as np
import pytest

from fhs.application.optimization_service import PortfolioOptimizer
from fhs.core.model import Feature
from fhs.core.model.value_objects import Budget, OptimizationStrategy
from fhs.core.services import FeatureSimulator, RiskCalculator


@pytest.fixture
def sample_features():
    """Create 3 sample features for testing."""
    return [
        Feature(
            name="Feature A",
            expected_users=5_000,
            conversion_rate=0.25,
            uncertainty=0.15,
            business_value_per_conversion=120.0,
            development_cost=45_000,
            dependency_cluster="Team Alpha",
            annual_growth_rate=0.20,
        ),
        Feature(
            name="Feature B",
            expected_users=12_000,
            conversion_rate=0.18,
            uncertainty=0.30,
            business_value_per_conversion=80.0,
            development_cost=60_000,
            dependency_cluster="Team Beta",
            annual_growth_rate=0.30,
        ),
        Feature(
            name="Feature C",
            expected_users=8_000,
            conversion_rate=0.22,
            uncertainty=0.20,
            business_value_per_conversion=95.0,
            development_cost=35_000,
            dependency_cluster="Team Gamma",
            annual_growth_rate=0.10,
        ),
    ]


@pytest.fixture
def simulation_results(sample_features):
    """Generate simulation results for sample features."""
    simulator = FeatureSimulator(seed=42)
    results = {}

    for feature in sample_features:
        result = simulator.simulate_feature(
            feature, scenarios=1000, distribution="normal"
        )
        results[feature.name] = result

    return results


@pytest.fixture
def optimizer(sample_features, simulation_results):
    """Create optimizer instance."""
    return PortfolioOptimizer(
        features=sample_features,
        simulation_results=simulation_results,
        risk_calculator=RiskCalculator(),
    )


def sum_portfolio_scenarios(combo_results, features):
    """Simple portfolio aggregation for testing."""
    arrays = []
    for name, result in combo_results.items():
        feature = next(f for f in features if f.name == name)
        bv = feature.business_value_per_conversion
        arrays.append(result.results_array * bv)
    return np.sum(arrays, axis=0)


class TestExactSolver:
    """Test suite for Exact (Brute-Force) Solver."""

    def test_exact_solver_basic(self, optimizer, sample_features):
        """Test exact solver with valid budget."""

        def sum_fn(combo_results):
            return sum_portfolio_scenarios(combo_results, sample_features)

        result = optimizer.optimize_exact(
            budget=100_000, strategy="var_floor", sum_portfolio_scenarios_fn=sum_fn
        )

        assert "recommended_features" in result
        assert "total_cost" in result
        assert "portfolio_expected" in result
        assert "portfolio_var_95" in result
        assert "computation_time_sec" in result
        assert "solver" in result
        assert result.solver == "exact"

        # Verify budget constraint
        assert result.total_cost <= 100_000

        # Verify selected features are valid
        assert len(result.recommended_features) > 0
        for name in result.recommended_features:
            assert name in [f.name for f in sample_features]

    def test_exact_solver_insufficient_budget(self, optimizer, sample_features):
        """Test exact solver with budget too small for any feature."""

        def sum_fn(combo_results):
            return sum_portfolio_scenarios(combo_results, sample_features)

        result = optimizer.optimize_exact(
            budget=10_000,  # Too small for any feature
            strategy="var_floor",
            sum_portfolio_scenarios_fn=sum_fn,
        )

        assert result.recommended_features == []
        assert result.total_cost == 0.0
        assert "message" in result

    def test_exact_solver_all_strategies(self, optimizer, sample_features):
        """Test all optimization strategies."""

        def sum_fn(combo_results):
            return sum_portfolio_scenarios(combo_results, sample_features)

        strategies = ["var_floor", "expected", "sharpe"]

        for strategy in strategies:
            result = optimizer.optimize_exact(
                budget=100_000, strategy=strategy, sum_portfolio_scenarios_fn=sum_fn
            )

            assert result.strategy == strategy
            assert len(result.recommended_features) > 0
            assert result.total_cost <= 100_000

    def test_exact_solver_accepts_value_objects(self, optimizer, sample_features):
        """Optimizer accepts Budget and OptimizationStrategy value objects."""

        def sum_fn(combo_results):
            return sum_portfolio_scenarios(combo_results, sample_features)

        result = optimizer.optimize_exact(
            budget=Budget(amount=100_000.0),
            strategy=OptimizationStrategy.EXPECTED,
            sum_portfolio_scenarios_fn=sum_fn,
        )

        assert result.strategy == "expected"
        assert result.budget == pytest.approx(100_000.0)
        assert result.total_cost <= 100_000

    def test_exact_solver_invalid_strategy(self, optimizer, sample_features):
        """Test exact solver with invalid strategy."""

        def sum_fn(combo_results):
            return sum_portfolio_scenarios(combo_results, sample_features)

        with pytest.raises(ValueError, match="Unknown strategy"):
            optimizer.optimize_exact(
                budget=100_000, strategy="invalid", sum_portfolio_scenarios_fn=sum_fn
            )

    def test_exact_solver_large_budget(self, optimizer, sample_features):
        """Test exact solver with budget large enough for all features."""

        def sum_fn(combo_results):
            return sum_portfolio_scenarios(combo_results, sample_features)

        result = optimizer.optimize_exact(
            budget=200_000,  # Enough for all features
            strategy="var_floor",
            sum_portfolio_scenarios_fn=sum_fn,
        )

        # Should select all 3 features
        assert len(result.recommended_features) == 3

    def test_exact_solver_performance(self, optimizer, sample_features):
        """Test that exact solver completes quickly for 3 features."""

        def sum_fn(combo_results):
            return sum_portfolio_scenarios(combo_results, sample_features)

        result = optimizer.optimize_exact(
            budget=100_000, strategy="var_floor", sum_portfolio_scenarios_fn=sum_fn
        )

        # Should complete in < 0.1 seconds for 3 features
        assert result.computation_time_sec < 0.1


class TestGreedySolver:
    """Test suite for Greedy solver."""

    def test_greedy_solver_basic(self, optimizer, sample_features):
        """Test greedy solver with valid budget."""

        def sum_fn(combo_results):
            return sum_portfolio_scenarios(combo_results, sample_features)

        result = optimizer.optimize_greedy(
            budget=100_000,
            strategy="var_floor",
            k=10,
            sum_portfolio_scenarios_fn=sum_fn,
        )

        assert "recommended_features" in result
        assert "total_cost" in result
        assert "portfolio_expected" in result
        assert "portfolio_var_95" in result
        assert "computation_time_sec" in result
        assert "solver" in result
        assert result.solver == "greedy"

        # Verify budget constraint
        assert result.total_cost <= 100_000

        # Verify selected features are valid
        assert len(result.recommended_features) > 0

    def test_greedy_solver_insufficient_budget(self, optimizer, sample_features):
        """Test greedy solver with budget too small."""

        def sum_fn(combo_results):
            return sum_portfolio_scenarios(combo_results, sample_features)

        result = optimizer.optimize_greedy(
            budget=10_000, strategy="var_floor", sum_portfolio_scenarios_fn=sum_fn
        )

        assert result.recommended_features == []
        assert result.total_cost == 0.0

    def test_greedy_solver_all_strategies(self, optimizer, sample_features):
        """Test all optimization strategies."""

        def sum_fn(combo_results):
            return sum_portfolio_scenarios(combo_results, sample_features)

        strategies = ["var_floor", "expected", "sharpe"]

        for strategy in strategies:
            result = optimizer.optimize_greedy(
                budget=100_000,
                strategy=strategy,
                k=5,
                sum_portfolio_scenarios_fn=sum_fn,
            )

            assert result.strategy == strategy
            assert result.total_cost <= 100_000

    def test_greedy_solver_performance(self, optimizer, sample_features):
        """Test that greedy solver completes quickly."""

        def sum_fn(combo_results):
            return sum_portfolio_scenarios(combo_results, sample_features)

        result = optimizer.optimize_greedy(
            budget=100_000,
            strategy="var_floor",
            k=10,
            sum_portfolio_scenarios_fn=sum_fn,
        )

        # Should complete in < 0.1 seconds
        assert result.computation_time_sec < 0.1

    def test_greedy_solver_k_values(self, optimizer, sample_features):
        """Test greedy solver with different k values."""

        def sum_fn(combo_results):
            return sum_portfolio_scenarios(combo_results, sample_features)

        for k in [1, 5, 10, 20]:
            result = optimizer.optimize_greedy(
                budget=100_000,
                strategy="var_floor",
                k=k,
                sum_portfolio_scenarios_fn=sum_fn,
            )

            # More candidates should not produce worse results
            assert result.total_cost <= 100_000
            assert result.combinations_evaluated >= 1


class TestExactVsGreedy:
    """Compare Exact and Greedy solvers."""

    def test_solvers_same_selection(self, optimizer, sample_features):
        """Test that both solvers find equivalent solutions for small portfolios."""

        def sum_fn(combo_results):
            return sum_portfolio_scenarios(combo_results, sample_features)

        exact = optimizer.optimize_exact(
            budget=100_000, strategy="var_floor", sum_portfolio_scenarios_fn=sum_fn
        )

        hybrid = optimizer.optimize_greedy(
            budget=100_000,
            strategy="var_floor",
            k=20,
            sum_portfolio_scenarios_fn=sum_fn,
            seed=42,  # Determinismus für reproduzierbare Tests
        )

        # Solutions should be equivalent (not necessarily identical)
        # Both should be within budget
        assert exact.total_cost <= 100_000
        assert hybrid.total_cost <= 100_000

        # Greedy should be at least as good as or nearly as good as exact
        # (within 5% tolerance for small test portfolios)
        if exact.portfolio_var_95 > 0:
            var_ratio = hybrid.portfolio_var_95 / exact.portfolio_var_95
            assert var_ratio >= 0.95, (
                f"Greedy solution significantly worse: "
                f"exact VaR={exact['portfolio_var_95']:.2f}, "
                f"greedy VaR={hybrid['portfolio_var_95']:.2f}"
            )

        # Number of selected features should be reasonable
        assert len(hybrid.recommended_features) > 0
        assert len(exact.recommended_features) > 0

    def test_greedy_faster_than_exact_large_portfolio(self):
        """Test that greedy is faster than exact for larger portfolios."""
        # Create 10 features
        features = [
            Feature(
                name=f"Feature {i}",
                expected_users=5000 + i * 1000,
                conversion_rate=0.2 + i * 0.01,
                uncertainty=0.15,
                business_value_per_conversion=100.0,
                development_cost=30_000 + i * 5_000,
            )
            for i in range(10)
        ]

        # Run simulations
        simulator = FeatureSimulator(seed=42)
        results = {
            f.name: simulator.simulate_feature(f, scenarios=1000) for f in features
        }

        optimizer = PortfolioOptimizer(
            features=features,
            simulation_results=results,
            risk_calculator=RiskCalculator(),
        )

        def sum_fn(combo_results):
            return sum_portfolio_scenarios(combo_results, features)

        exact = optimizer.optimize_exact(
            budget=200_000, strategy="var_floor", sum_portfolio_scenarios_fn=sum_fn
        )

        hybrid = optimizer.optimize_greedy(
            budget=200_000,
            strategy="var_floor",
            k=10,
            sum_portfolio_scenarios_fn=sum_fn,
        )

        # Hybrid should be faster
        assert hybrid.computation_time_sec < exact.computation_time_sec


class TestSimpleSumFallback:
    """Test the simple sum fallback when no portfolio function is provided."""

    def test_exact_solver_without_sum_function(self, optimizer):
        """Test exact solver with default simple sum."""
        result = optimizer.optimize_exact(
            budget=100_000,
            strategy="var_floor",
            # No sum_portfolio_scenarios_fn provided
        )

        assert len(result.recommended_features) > 0
        assert result.total_cost <= 100_000

    def test_greedy_solver_without_sum_function(self, optimizer):
        """Test greedy solver with default simple sum."""
        result = optimizer.optimize_greedy(
            budget=100_000,
            strategy="var_floor",
            k=5,
            # No sum_portfolio_scenarios_fn provided
        )

        assert len(result.recommended_features) > 0
        assert result.total_cost <= 100_000


# ── Fixtures with delivery risk ───────────────────────────────────────


@pytest.fixture
def features_with_delivery_risk():
    """Create features with non-zero likelihood_of_non_delivery."""
    return [
        Feature(
            name="Safe Feature",
            expected_users=5_000,
            conversion_rate=0.25,
            uncertainty=0.15,
            business_value_per_conversion=120.0,
            development_cost=45_000,
            likelihood_of_non_delivery=0.05,
        ),
        Feature(
            name="Risky Feature",
            expected_users=12_000,
            conversion_rate=0.18,
            uncertainty=0.30,
            business_value_per_conversion=80.0,
            development_cost=60_000,
            likelihood_of_non_delivery=0.40,
        ),
        Feature(
            name="Medium Feature",
            expected_users=8_000,
            conversion_rate=0.22,
            uncertainty=0.20,
            business_value_per_conversion=95.0,
            development_cost=35_000,
            likelihood_of_non_delivery=0.20,
        ),
    ]


@pytest.fixture
def delivery_optimizer(features_with_delivery_risk):
    """Optimizer with delivery-risk features and simulation results."""
    simulator = FeatureSimulator(seed=42)
    results = {
        f.name: simulator.simulate_feature(f, scenarios=10_000)
        for f in features_with_delivery_risk
    }
    return PortfolioOptimizer(
        features=features_with_delivery_risk,
        simulation_results=results,
        risk_calculator=RiskCalculator(),
    )


class TestDeliveryRiskAnalysis:
    """Test suite for analyze_delivery_risk."""

    def test_returns_required_keys(self, delivery_optimizer):
        """All expected keys are present in the result."""
        solver_result = delivery_optimizer.optimize_exact(budget=200_000)
        dr = delivery_optimizer.analyze_delivery_risk(solver_result)

        required_keys = {
            "solver",
            "features",
            "market_expected",
            "market_var_95",
            "analytical_expected",
            "simulated_expected",
            "simulated_var_95",
            "exp_delta_pct",
            "var_delta_pct",
        }
        assert required_keys.issubset(dr.keys())

    def test_analytical_close_to_simulated_expected(self, delivery_optimizer):
        """Analytical and simulated expected business value converge."""
        solver_result = delivery_optimizer.optimize_exact(budget=200_000)
        dr = delivery_optimizer.analyze_delivery_risk(solver_result)

        # With 10,000 scenarios, analytical and simulated should be within 3%
        if dr["analytical_expected"] > 0:
            diff_pct = (
                abs(dr["analytical_expected"] - dr["simulated_expected"])
                / dr["analytical_expected"]
            )
            assert diff_pct < 0.03, (
                f"Analytical ({dr['analytical_expected']:.0f}) vs "
                f"Simulated ({dr['simulated_expected']:.0f}) differ by {diff_pct:.1%}"
            )

    def test_delivery_risk_reduces_expected_business_value(self, delivery_optimizer):
        """With non-zero delivery risk, expected business value must drop."""
        solver_result = delivery_optimizer.optimize_exact(budget=200_000)
        dr = delivery_optimizer.analyze_delivery_risk(solver_result)

        assert dr["simulated_expected"] < dr["market_expected"]
        assert dr["analytical_expected"] < dr["market_expected"]
        assert dr["exp_delta_pct"] < 0

    def test_delivery_risk_reduces_var(self, delivery_optimizer):
        """VaR 95% should also drop when delivery risk is applied."""
        solver_result = delivery_optimizer.optimize_exact(budget=200_000)
        dr = delivery_optimizer.analyze_delivery_risk(solver_result)

        assert dr["simulated_var_95"] < dr["market_var_95"]
        assert dr["var_delta_pct"] < 0

    def test_zero_delivery_risk_no_change(
        self, sample_features, simulation_results, optimizer
    ):
        """With likelihood_of_non_delivery=0, results should be unchanged."""
        # sample_features have default likelihood_of_non_delivery=0.0
        solver_result = optimizer.optimize_exact(budget=200_000)
        dr = optimizer.analyze_delivery_risk(solver_result)

        assert dr["analytical_expected"] == pytest.approx(
            dr["market_expected"], rel=1e-6
        )
        assert dr["simulated_expected"] == pytest.approx(
            dr["market_expected"], rel=1e-6
        )
        assert dr["simulated_var_95"] == pytest.approx(dr["market_var_95"], rel=1e-6)

    def test_per_feature_details(self, delivery_optimizer):
        """Feature details include correct non-delivery risk values."""
        solver_result = delivery_optimizer.optimize_exact(budget=200_000)
        dr = delivery_optimizer.analyze_delivery_risk(solver_result)

        assert len(dr["features"]) > 0
        for fd in dr["features"]:
            assert "name" in fd
            assert "non_delivery_risk" in fd
            assert "delivered_pct" in fd
            assert 0.0 <= fd["delivered_pct"] <= 1.0

    def test_high_risk_feature_delivered_less(self, delivery_optimizer):
        """A feature with 40% non-delivery risk is delivered ~60% of the time."""
        solver_result = delivery_optimizer.optimize_exact(budget=200_000)
        dr = delivery_optimizer.analyze_delivery_risk(solver_result)

        risky = next(f for f in dr["features"] if f["name"] == "Risky Feature")
        # With 10,000 scenarios, delivered_pct should be close to 0.60
        assert 0.55 < risky["delivered_pct"] < 0.65

    def test_empty_portfolio(self, delivery_optimizer):
        """Delivery risk analysis handles empty portfolio gracefully."""
        empty_result = {"recommended_features": [], "solver": "exact"}
        dr = delivery_optimizer.analyze_delivery_risk(empty_result)

        assert dr["features"] == []
        assert dr["market_expected"] == 0.0
        assert dr["simulated_expected"] == 0.0

    def test_reproducible_with_seed(self, delivery_optimizer):
        """Same seed produces identical results."""
        solver_result = delivery_optimizer.optimize_exact(budget=200_000)
        dr1 = delivery_optimizer.analyze_delivery_risk(solver_result, seed=123)
        dr2 = delivery_optimizer.analyze_delivery_risk(solver_result, seed=123)

        assert dr1["simulated_expected"] == dr2["simulated_expected"]
        assert dr1["simulated_var_95"] == dr2["simulated_var_95"]

    def test_different_seed_different_results(self, delivery_optimizer):
        """Different seeds produce different results (not identical)."""
        solver_result = delivery_optimizer.optimize_exact(budget=200_000)
        dr1 = delivery_optimizer.analyze_delivery_risk(solver_result, seed=1)
        dr2 = delivery_optimizer.analyze_delivery_risk(solver_result, seed=99)

        # Simulated values should differ slightly due to different RNG draws
        assert dr1["simulated_var_95"] != dr2["simulated_var_95"]


class TestSystematicShock:
    """Test suite for systematic shock in analyze_delivery_risk."""

    def test_no_shock_by_default(self, delivery_optimizer):
        """Without shock parameters, no shock keys are returned."""
        solver_result = delivery_optimizer.optimize_exact(budget=200_000)
        dr = delivery_optimizer.analyze_delivery_risk(solver_result)

        assert "shocked_expected" not in dr
        assert "shocked_var_95" not in dr

    def test_shock_keys_present(self, delivery_optimizer):
        """With shock > 0, shock keys are returned."""
        solver_result = delivery_optimizer.optimize_exact(budget=200_000)
        dr = delivery_optimizer.analyze_delivery_risk(
            solver_result,
            systematic_shock_probability=0.05,
            systematic_shock_multiplier=0.3,
        )

        assert "shocked_expected" in dr
        assert "shocked_var_95" in dr
        assert "shock_probability" in dr
        assert "shock_multiplier" in dr
        assert "shock_hit_pct" in dr

    def test_shock_reduces_var_more_than_delivery(self, delivery_optimizer):
        """Systematic shock should reduce VaR 95% further than delivery risk alone."""
        solver_result = delivery_optimizer.optimize_exact(budget=200_000)
        dr = delivery_optimizer.analyze_delivery_risk(
            solver_result,
            systematic_shock_probability=0.10,
            systematic_shock_multiplier=0.2,
        )

        # Shock VaR should be lower than delivery-only VaR
        assert dr["shocked_var_95"] < dr["simulated_var_95"]
        # And both lower than market-only
        assert dr["simulated_var_95"] < dr["market_var_95"]

    def test_shock_hit_pct_near_probability(self, delivery_optimizer):
        """With 10,000 scenarios, shock hit rate should be near configured probability."""
        solver_result = delivery_optimizer.optimize_exact(budget=200_000)
        dr = delivery_optimizer.analyze_delivery_risk(
            solver_result,
            systematic_shock_probability=0.10,
        )

        # With 10,000 scenarios, should be within 3 percentage points
        assert 0.07 < dr["shock_hit_pct"] < 0.13

    def test_zero_multiplier_wipes_business_value(self, delivery_optimizer):
        """A shock multiplier of 0 should produce VaR 95% = 0 when shock probability is high."""
        solver_result = delivery_optimizer.optimize_exact(budget=200_000)
        dr = delivery_optimizer.analyze_delivery_risk(
            solver_result,
            systematic_shock_probability=0.50,
            systematic_shock_multiplier=0.0,
        )

        # With 50% of scenarios at zero business value, VaR 95% must be 0
        assert dr["shocked_var_95"] == pytest.approx(0.0, abs=1.0)

    def test_shock_expected_less_than_delivery(self, delivery_optimizer):
        """Shocked expected business value should be less than delivery-only expected."""
        solver_result = delivery_optimizer.optimize_exact(budget=200_000)
        dr = delivery_optimizer.analyze_delivery_risk(
            solver_result,
            systematic_shock_probability=0.05,
            systematic_shock_multiplier=0.3,
        )

        assert dr["shocked_expected"] < dr["simulated_expected"]


class TestBudgetRiskProfiles:
    """Test suite for analyze_budget_risk_profiles."""

    def test_returns_budget_keys(self, delivery_optimizer):
        budgets = [80_000, 140_000, 200_000]

        result = delivery_optimizer.analyze_budget_risk_profiles(
            budgets,
            systematic_shock_probability=0.05,
            systematic_shock_multiplier=0.3,
        )

        assert set(result.keys()) == {80_000, 140_000, 200_000}

    def test_returns_solver_entries_with_levels(self, delivery_optimizer):
        result = delivery_optimizer.analyze_budget_risk_profiles(
            [200_000],
            systematic_shock_probability=0.05,
            systematic_shock_multiplier=0.3,
        )

        solver_data = result[200_000]["exact"]
        assert "solver_result" in solver_data
        assert "feature_count" in solver_data
        assert "l1" in solver_data
        assert "l3" in solver_data
        assert solver_data["feature_count"] > 0

    def test_ilp_solver_can_be_requested(self, delivery_optimizer):
        result = delivery_optimizer.analyze_budget_risk_profiles(
            [200_000],
            solvers=("ilp",),
            systematic_shock_probability=0.05,
            systematic_shock_multiplier=0.3,
        )

        assert set(result[200_000].keys()) == {"ilp"}

    def test_invalid_solver_raises(self, delivery_optimizer):
        with pytest.raises(ValueError, match="Unknown solver"):
            delivery_optimizer.analyze_budget_risk_profiles([200_000], solvers=("bad",))

    def test_shock_level_is_worse_than_delivery_level(self, delivery_optimizer):
        result = delivery_optimizer.analyze_budget_risk_profiles(
            [200_000],
            systematic_shock_probability=0.05,
            systematic_shock_multiplier=0.3,
        )

        exact_data = result[200_000]["exact"]
        assert exact_data["l3"]["shocked_var_95"] < exact_data["l1"]["simulated_var_95"]

    def test_budget_too_small_to_select_any_feature_skips_solver_entry(
        self, delivery_optimizer
    ):
        result = delivery_optimizer.analyze_budget_risk_profiles(
            [1.0],
            solvers=("exact",),
        )
        # With budget=1.0 no feature can be selected → continue branch hit → empty dict
        assert result[1.0] == {}
