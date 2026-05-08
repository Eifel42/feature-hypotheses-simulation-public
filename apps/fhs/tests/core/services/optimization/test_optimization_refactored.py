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
Tests for Refactored Optimization Architecture

Demonstrates testing patterns for the new DDD-based design:
- Isolated solver tests
- Strategy pattern tests
- Protocol compliance tests
"""

import numpy as np
import numpy_financial as npf
import pytest

from fhs.core.model import Feature, SimulationResult
from fhs.core.services import RiskCalculator
from fhs.core.services.optimization import (
    DeliveryRiskAnalyzer,
    ExactSolver,
    GreedySolver,
    ILPSolver,
    ObjectiveFunctionFactory,
    PortfolioMetrics,
    PortfolioMetricsCalculator,
    PortfolioResult,
)

# ────────────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def simple_features():
    """Two simple features for testing."""
    return [
        Feature(
            name="Feature A",
            expected_users=5000,
            conversion_rate=0.25,
            uncertainty=0.15,
            development_cost=10000,
            business_value_per_conversion=100,
            likelihood_of_non_delivery=0.1,
        ),
        Feature(
            name="Feature B",
            expected_users=8000,
            conversion_rate=0.30,
            uncertainty=0.20,
            development_cost=15000,
            business_value_per_conversion=150,
            likelihood_of_non_delivery=0.15,
        ),
    ]


@pytest.fixture
def simple_simulation_results():
    """Simple simulation results for testing."""
    np.random.seed(42)
    return {
        "Feature A": SimulationResult(
            feature_name="Feature A",
            results=np.random.normal(100, 20, 1000),
            scenarios=1000,
            expected_value=100.0,
            business_value_per_conversion=100,
            development_cost=10000,
        ),
        "Feature B": SimulationResult(
            feature_name="Feature B",
            results=np.random.normal(150, 30, 1000),
            scenarios=1000,
            expected_value=150.0,
            business_value_per_conversion=150,
            development_cost=15000,
        ),
    }


@pytest.fixture
def risk_calculator():
    """Risk calculator instance."""
    return RiskCalculator()


# ────────────────────────────────────────────────────────────────────────────
# Test: Strategy Pattern (Objective Functions)
# ────────────────────────────────────────────────────────────────────────────


def test_objective_function_factory_creates_var_floor():
    """Test factory creates VarFloor strategy."""
    obj_fn = ObjectiveFunctionFactory.create("var_floor")
    assert obj_fn.name == "var_floor"


def test_objective_function_factory_creates_expected():
    """Test factory creates Expected strategy."""
    obj_fn = ObjectiveFunctionFactory.create("expected")
    assert obj_fn.name == "expected"


def test_objective_function_factory_creates_sharpe():
    """Test factory creates Sharpe strategy."""
    obj_fn = ObjectiveFunctionFactory.create("sharpe")
    assert obj_fn.name == "sharpe"


def test_objective_function_factory_creates_npv_year1():
    """Test factory creates NPV Year-1 strategy."""
    obj_fn = ObjectiveFunctionFactory.create("npv_year1", discount_rate=0.08)
    assert obj_fn.name == "npv_year1"


def test_objective_function_factory_creates_npv_3year():
    """Test factory creates NPV 3-year strategy."""
    obj_fn = ObjectiveFunctionFactory.create("npv_3year", discount_rate=0.08)
    assert obj_fn.name == "npv_3year"


def test_objective_function_factory_raises_on_unknown():
    """Test factory raises ValueError for unknown strategy."""
    with pytest.raises(ValueError, match="Unknown strategy"):
        ObjectiveFunctionFactory.create("invalid_strategy")


def test_var_floor_objective_scores_portfolio_by_var95():
    """Test VarFloor strategy scores by VaR95."""
    obj_fn = ObjectiveFunctionFactory.create("var_floor")
    metrics = PortfolioMetrics(expected=100, var_95=80, cvar_95=70, std_dev=15)
    score = obj_fn.score_portfolio(metrics)
    assert score == 80  # VaR95


def test_expected_objective_scores_portfolio_by_expected():
    """Test Expected strategy scores by expected business value."""
    obj_fn = ObjectiveFunctionFactory.create("expected")
    metrics = PortfolioMetrics(expected=100, var_95=80, cvar_95=70, std_dev=15)
    score = obj_fn.score_portfolio(metrics)
    assert score == 100  # Expected


def test_sharpe_objective_scores_portfolio_by_sharpe_ratio():
    """Test Sharpe strategy scores by risk-adjusted return."""
    obj_fn = ObjectiveFunctionFactory.create("sharpe")
    metrics = PortfolioMetrics(expected=100, var_95=80, cvar_95=70, std_dev=20)
    score = obj_fn.score_portfolio(metrics)
    assert score == 5.0  # 100 / 20


def test_sharpe_objective_handles_zero_std_dev():
    """Test Sharpe strategy handles zero std_dev gracefully."""
    obj_fn = ObjectiveFunctionFactory.create("sharpe")
    metrics = PortfolioMetrics(expected=100, var_95=80, cvar_95=70, std_dev=0.0)
    score = obj_fn.score_portfolio(metrics)
    assert score == 0.0  # Safe fallback


def test_npv_year1_objective_scores_feature_with_discounting(
    simple_features, simple_simulation_results
):
    """Test Year-1 NPV score equals discounted revenue minus development cost."""
    obj_fn = ObjectiveFunctionFactory.create("npv_year1", discount_rate=0.10)
    feature = simple_features[0]
    result = simple_simulation_results[feature.name]

    cashflows = [
        -feature.development_cost,
        result.expected_business_value - feature.annual_operating_cost,
    ]
    expected_score = float(npf.npv(0.10, cashflows))
    score = obj_fn.score_feature(feature, result)

    assert score == pytest.approx(expected_score)


def test_npv_3year_objective_scores_feature_with_growth(simple_simulation_results):
    """Test 3-year NPV score applies growth and yearly discounting."""
    obj_fn = ObjectiveFunctionFactory.create("npv_3year", discount_rate=0.08)
    feature = Feature(
        name="Growth Feature",
        expected_users=1000,
        conversion_rate=0.20,
        uncertainty=0.10,
        development_cost=12_000,
        revenue_per_conversion=100,
        annual_growth_rate=0.15,
        likelihood_of_non_delivery=0.05,
    )
    result = simple_simulation_results["Feature A"]

    base = result.expected_business_value
    cashflows = [
        -feature.development_cost,
        base - feature.annual_operating_cost,
        base * 1.15 - feature.annual_operating_cost,
        base * (1.15**2) - feature.annual_operating_cost,
    ]
    expected_score = float(npf.npv(0.08, cashflows))
    score = obj_fn.score_feature(feature, result)

    assert score == pytest.approx(expected_score)


# ────────────────────────────────────────────────────────────────────────────
# Test: Portfolio Metrics Calculator
# ────────────────────────────────────────────────────────────────────────────


def test_portfolio_metrics_calculator_computes_all_metrics(risk_calculator):
    """Test metrics calculator computes all metrics correctly."""
    calc = PortfolioMetricsCalculator(risk_calculator)
    scenarios = np.array([100, 120, 80, 150, 110])

    metrics = calc.calculate(scenarios)

    assert metrics.expected == pytest.approx(112.0)
    assert metrics.std_dev > 0
    assert metrics.var_95 < metrics.expected  # VaR should be lower than mean
    assert metrics.cvar_95 <= metrics.var_95  # CVaR should be lower than VaR


def test_portfolio_metrics_sharpe_ratio():
    """Test PortfolioMetrics computes Sharpe ratio."""
    metrics = PortfolioMetrics(expected=100, var_95=80, cvar_95=70, std_dev=20)
    assert metrics.sharpe_ratio == 5.0


# ────────────────────────────────────────────────────────────────────────────
# Test: ExactSolver
# ────────────────────────────────────────────────────────────────────────────


def test_exact_solver_returns_portfolio_result(
    simple_features, simple_simulation_results, risk_calculator
):
    """Test ExactSolver returns PortfolioResult."""
    solver = ExactSolver(risk_calculator)
    result = solver.optimize(
        features=simple_features,
        simulation_results=simple_simulation_results,
        budget=20000,
        strategy="expected",
    )

    assert isinstance(result, PortfolioResult)
    assert result.solver == "exact"
    assert result.total_cost <= 20000
    assert result.feature_count >= 1


def test_exact_solver_respects_budget_constraint(
    simple_features, simple_simulation_results, risk_calculator
):
    """Test ExactSolver respects budget constraint."""
    solver = ExactSolver(risk_calculator)
    result = solver.optimize(
        features=simple_features,
        simulation_results=simple_simulation_results,
        budget=12000,  # Only Feature A fits
        strategy="var_floor",
    )

    assert result.total_cost <= 12000
    assert "Feature A" in result.recommended_features


def test_exact_solver_returns_empty_for_insufficient_budget(
    simple_features, simple_simulation_results, risk_calculator
):
    """Test ExactSolver returns empty result for insufficient budget."""
    solver = ExactSolver(risk_calculator)
    result = solver.optimize(
        features=simple_features,
        simulation_results=simple_simulation_results,
        budget=5000,  # Too low
        strategy="var_floor",
    )

    assert result.feature_count == 0
    assert result.total_cost == 0
    assert result.message is not None


# ────────────────────────────────────────────────────────────────────────────
# Test: GreedySolver
# ────────────────────────────────────────────────────────────────────────────


def test_greedy_solver_returns_portfolio_result(
    simple_features, simple_simulation_results, risk_calculator
):
    """Test GreedySolver returns PortfolioResult."""
    solver = GreedySolver(risk_calculator)
    result = solver.optimize(
        features=simple_features,
        simulation_results=simple_simulation_results,
        budget=20000,
        strategy="expected",
        k_candidates=5,
    )

    assert isinstance(result, PortfolioResult)
    assert result.solver == "greedy"
    assert result.total_cost <= 20000


def test_greedy_solver_includes_metadata(
    simple_features, simple_simulation_results, risk_calculator
):
    """Test GreedySolver includes timing metadata."""
    solver = GreedySolver(risk_calculator)
    result = solver.optimize(
        features=simple_features,
        simulation_results=simple_simulation_results,
        budget=20000,
        strategy="sharpe",
        k_candidates=3,
    )

    assert result.metadata is not None
    assert "greedy_time_sec" in result.metadata
    assert "simulation_time_sec" in result.metadata
    assert "k_candidates" in result.metadata


def test_greedy_solver_validates_k_candidates(
    simple_features, simple_simulation_results, risk_calculator
):
    """Test GreedySolver validates k_candidates parameter."""
    solver = GreedySolver(risk_calculator)

    with pytest.raises(ValueError, match="k_candidates must be"):
        solver.optimize(
            features=simple_features,
            simulation_results=simple_simulation_results,
            budget=20000,
            strategy="var_floor",
            k_candidates=0,  # Invalid
        )


# ────────────────────────────────────────────────────────────────────────────
# Test: ILPSolver
# ────────────────────────────────────────────────────────────────────────────


def test_ilp_solver_returns_portfolio_result(
    simple_features, simple_simulation_results, risk_calculator
):
    """Test ILPSolver returns PortfolioResult."""
    solver = ILPSolver(risk_calculator)
    result = solver.optimize(
        features=simple_features,
        simulation_results=simple_simulation_results,
        budget=20000,
        strategy="expected",
    )

    assert isinstance(result, PortfolioResult)
    assert result.solver == "ilp"
    assert result.total_cost <= 20000


def test_ilp_solver_uses_scipy_milp(
    simple_features, simple_simulation_results, risk_calculator
):
    """Test ILPSolver uses scipy.optimize.milp internally."""
    solver = ILPSolver(risk_calculator)
    result = solver.optimize(
        features=simple_features,
        simulation_results=simple_simulation_results,
        budget=25000,
        strategy="var_floor",
    )

    assert result.metadata is not None
    assert "ilp_status" in result.metadata
    assert "ilp_message" in result.metadata


# ────────────────────────────────────────────────────────────────────────────
# Test: DeliveryRiskAnalyzer
# ────────────────────────────────────────────────────────────────────────────


def test_delivery_risk_analyzer_analyzes_portfolio(
    simple_features, simple_simulation_results, risk_calculator
):
    """Test DeliveryRiskAnalyzer analyzes delivery risk."""
    solver = ExactSolver(risk_calculator)
    result = solver.optimize(
        features=simple_features,
        simulation_results=simple_simulation_results,
        budget=20000,
        strategy="expected",
    )

    analyzer = DeliveryRiskAnalyzer(simple_features, simple_simulation_results)
    risk_analysis = analyzer.analyze(result, seed=42)

    assert "market_expected" in risk_analysis
    assert "simulated_expected" in risk_analysis
    assert "analytical_expected" in risk_analysis
    assert "features" in risk_analysis
    assert len(risk_analysis["features"]) == result.feature_count


def test_delivery_risk_analyzer_applies_systematic_shock(
    simple_features, simple_simulation_results, risk_calculator
):
    """Test DeliveryRiskAnalyzer applies systematic shock."""
    solver = ExactSolver(risk_calculator)
    result = solver.optimize(
        features=simple_features,
        simulation_results=simple_simulation_results,
        budget=20000,
        strategy="expected",
    )

    analyzer = DeliveryRiskAnalyzer(simple_features, simple_simulation_results)
    risk_analysis = analyzer.analyze(
        result,
        seed=42,
        systematic_shock_probability=0.1,
        systematic_shock_multiplier=0.5,
    )

    assert "shocked_expected" in risk_analysis
    assert "shocked_var_95" in risk_analysis
    assert "shock_probability" in risk_analysis
    assert risk_analysis["shocked_expected"] < risk_analysis["market_expected"]


# ────────────────────────────────────────────────────────────────────────────
# Test: Protocol Compliance
# ────────────────────────────────────────────────────────────────────────────


def test_all_solvers_satisfy_protocol(risk_calculator):
    """Test all solvers satisfy PortfolioSolver protocol."""
    from fhs.core.services.optimization.domain import PortfolioSolver

    solvers = [
        ExactSolver(risk_calculator),
        GreedySolver(risk_calculator),
        ILPSolver(risk_calculator),
    ]

    for solver in solvers:
        assert isinstance(solver, PortfolioSolver)
        assert hasattr(solver, "optimize")
        assert hasattr(solver, "name")


# ────────────────────────────────────────────────────────────────────────────
# Test: PortfolioResult Value Object
# ────────────────────────────────────────────────────────────────────────────


def test_portfolio_result_is_immutable():
    """Test PortfolioResult is immutable (frozen)."""
    result = PortfolioResult(
        recommended_features=["A", "B"],
        total_cost=10000,
        portfolio_expected=50000,
        portfolio_var_95=40000,
        portfolio_cvar_95=35000,
        portfolio_std_dev=5000,
        budget=15000,
        budget_remaining=5000,
        solver="exact",
        strategy="var_floor",
        computation_time_sec=0.5,
        combinations_evaluated=10,
    )

    with pytest.raises(Exception):  # Pydantic ValidationError
        result.total_cost = 20000


def test_portfolio_result_computes_feature_count():
    """Test PortfolioResult computes feature count."""
    result = PortfolioResult(
        recommended_features=["A", "B", "C"],
        total_cost=10000,
        portfolio_expected=50000,
        portfolio_var_95=40000,
        portfolio_cvar_95=35000,
        portfolio_std_dev=5000,
        budget=15000,
        budget_remaining=5000,
        solver="exact",
        strategy="var_floor",
        computation_time_sec=0.5,
        combinations_evaluated=10,
    )

    assert result.feature_count == 3


def test_portfolio_result_computes_budget_utilization():
    """Test PortfolioResult computes budget utilization."""
    result = PortfolioResult(
        recommended_features=["A"],
        total_cost=8000,
        portfolio_expected=50000,
        portfolio_var_95=40000,
        portfolio_cvar_95=35000,
        portfolio_std_dev=5000,
        budget=10000,
        budget_remaining=2000,
        solver="exact",
        strategy="var_floor",
        computation_time_sec=0.5,
        combinations_evaluated=10,
    )

    assert result.budget_utilization == 0.8  # 8000 / 10000
