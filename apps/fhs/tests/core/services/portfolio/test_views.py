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

"""Tests for PortfolioViewService."""

import numpy as np
import pytest

from fhs.core.model.value_objects import OptimizationResult, PortfolioSnapshot
from fhs.core.services.optimization.domain import PortfolioResult
from fhs.core.services.portfolio.views import PortfolioViewService


def _optimization_result_for_budget(budget: float) -> OptimizationResult:
    return OptimizationResult(
        recommended_features=("A",),
        total_cost=budget * 0.8,
        portfolio_expected=budget * 1.1,
        portfolio_var_95=budget * 0.7,
        portfolio_cvar_95=budget * 0.6,
        portfolio_std_dev=10.0,
        budget=budget,
        budget_remaining=budget * 0.2,
        computation_time_sec=0.01,
        combinations_evaluated=1,
        solver="test",
        strategy="var_floor",
        portfolio_roi=0.1,
        roi=0.1,
        safety_buffer=5.0,
        message="ok",
        metadata={},
    )


def test_concentration_from_expected_business_values_returns_hhi_and_verdict() -> None:
    result = PortfolioViewService.concentration_from_expected_business_values(
        {"A": 70.0, "B": 30.0}
    )

    assert result.hhi == pytest.approx(0.58)
    assert result.verdict == "High concentration"
    assert sum(result.shares.values()) == pytest.approx(1.0)


def test_portfolio_snapshot_from_scenarios_builds_metrics() -> None:
    scenarios = np.array([100.0, 200.0, 300.0], dtype=float)
    result = PortfolioViewService.portfolio_snapshot_from_scenarios(
        scenarios,
        investment=50.0,
    )

    assert result.expected == pytest.approx(200.0)
    assert result.var_95 == pytest.approx(np.percentile(scenarios, 5))
    assert result.investment == pytest.approx(50.0)


def test_budget_frontier_rows_sorts_budgets() -> None:
    rows = PortfolioViewService.budget_frontier_rows(
        budgets=[300.0, 100.0, 200.0],
        optimize_for_budget=_optimization_result_for_budget,
    )

    assert [row.budget for row in rows] == [100.0, 200.0, 300.0]
    assert rows[0].selected_count == 1
    assert rows[0].expected == pytest.approx(110.0)


def test_optimization_result_from_solver_result_maps_fields() -> None:
    solver_result = PortfolioResult(
        recommended_features=["A", "B"],
        total_cost=100.0,
        portfolio_expected=140.0,
        portfolio_var_95=90.0,
        portfolio_cvar_95=80.0,
        portfolio_std_dev=12.0,
        budget=120.0,
        budget_remaining=20.0,
        solver="exact",
        strategy="var_floor",
        computation_time_sec=0.5,
        combinations_evaluated=8,
        message="ok",
        metadata={"x": 1},
    )

    result = PortfolioViewService.optimization_result_from_solver_result(solver_result)

    assert isinstance(result, OptimizationResult)
    assert result.recommended_features == ("A", "B")
    assert result.portfolio_roi == pytest.approx(0.4)
    assert result.safety_buffer == pytest.approx(-10.0)


def test_optimize_portfolio_dispatches_to_solver() -> None:
    class FakeOptimizer:
        @staticmethod
        def optimize_exact(**kwargs):
            return PortfolioResult(
                recommended_features=["A"],
                total_cost=80.0,
                portfolio_expected=100.0,
                portfolio_var_95=70.0,
                portfolio_cvar_95=60.0,
                portfolio_std_dev=10.0,
                budget=float(kwargs["budget"]),
                budget_remaining=float(kwargs["budget"]) - 80.0,
                solver="exact",
                strategy=str(kwargs["strategy"]),
                computation_time_sec=0.1,
                combinations_evaluated=3,
                message="ok",
                metadata={"solver": "exact"},
            )

        def optimize_ilp(self, **kwargs):
            raise AssertionError("not expected in this test")

        def optimize_greedy(self, **kwargs):
            raise AssertionError("not expected in this test")

    result = PortfolioViewService.optimize_portfolio(
        optimizer=FakeOptimizer(),
        solver="exact",
        budget=100.0,
        strategy="var_floor",
        sum_portfolio_scenarios_fn=lambda _: np.array([1.0], dtype=float),
        seed=42,
    )

    assert isinstance(result, OptimizationResult)
    assert result.solver == "exact"
    assert result.budget == pytest.approx(100.0)


def test_stress_scenarios_view_returns_named_scenarios() -> None:
    baseline = PortfolioSnapshot(
        expected=200.0,
        var_95=150.0,
        cvar_95=140.0,
        std_dev=20.0,
        investment=100.0,
    )
    components = {
        "A": np.array([100.0, 100.0], dtype=float),
        "B": np.array([100.0, 100.0], dtype=float),
    }

    result = PortfolioViewService.stress_scenarios_view(
        resolved=("A", "B"),
        baseline=baseline,
        components=components,
        top_feature="A",
        is_high_delivery_risk=lambda name: name == "B",
    )

    assert result["baseline"] == baseline
    scenarios = result["scenarios"]
    assert len(scenarios) == 3
    assert [scenario["name"] for scenario in scenarios] == [
        "Market pullback",
        "Top feature delay",
        "Execution pressure",
    ]


def test_dependency_correlation_view_returns_empty_for_no_labels() -> None:
    result = PortfolioViewService.dependency_correlation_view(
        labels=[],
        dependency_matrix=np.array([[]], dtype=float),
        business_value_arrays=np.array([[]], dtype=float),
    )

    assert result["labels"] == []
    assert result["average_corr"] == pytest.approx(0.0)


def test_dependency_correlation_view_returns_empirical_matrix() -> None:
    arrays = np.array(
        [
            [1.0, 2.0],
            [2.0, 3.0],
            [3.0, 4.0],
            [4.0, 5.0],
        ],
        dtype=float,
    )
    dependency_matrix = np.array([[1.0, 0.5], [0.5, 1.0]], dtype=float)

    result = PortfolioViewService.dependency_correlation_view(
        labels=["A", "B"],
        dependency_matrix=dependency_matrix,
        business_value_arrays=arrays,
    )

    assert result["labels"] == ["A", "B"]
    assert result["dependency_matrix"].shape == (2, 2)
    assert result["empirical_matrix"].shape == (2, 2)
    assert result["average_corr"] == pytest.approx(1.0)
