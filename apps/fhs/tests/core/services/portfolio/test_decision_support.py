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

"""Tests for PortfolioDecisionSupportService."""

from __future__ import annotations

import numpy as np
import pytest

from fhs.core.model import Feature, OptimizationResult, SimulationResult
from fhs.core.services.portfolio.decision_support import PortfolioDecisionSupportService


def _feature(
    name: str,
    *,
    cost: float,
    llp: float,
    cluster: str | None = None,
    business_value_per_conversion: float = 1.0,
) -> Feature:
    return Feature(
        name=name,
        expected_users=10_000,
        conversion_rate=0.25,
        uncertainty=0.10,
        business_value_per_conversion=business_value_per_conversion,
        development_cost=cost,
        annual_growth_rate=0.05,
        likelihood_of_non_delivery=llp,
        dependency_cluster=cluster,
    )


def _sim_result(
    name: str,
    values: np.ndarray,
    *,
    business_value_per_conversion: float,
    development_cost: float,
) -> SimulationResult:
    return SimulationResult(
        feature_name=name,
        results=values,
        expected_value=float(np.mean(values)),
        business_value_per_conversion=business_value_per_conversion,
        development_cost=development_cost,
    )


def _optimization_result(
    *,
    solver: str,
    recommended: tuple[str, ...],
    total_cost: float,
    portfolio_expected: float,
    portfolio_var_95: float,
    budget: float,
) -> OptimizationResult:
    return OptimizationResult(
        recommended_features=recommended,
        total_cost=total_cost,
        portfolio_expected=portfolio_expected,
        portfolio_var_95=portfolio_var_95,
        portfolio_cvar_95=portfolio_var_95,
        portfolio_std_dev=0.0,
        budget=budget,
        budget_remaining=budget - total_cost,
        computation_time_sec=0.0,
        combinations_evaluated=1,
        solver=solver,
        strategy="var_floor",
        portfolio_roi=0.0,
        roi=0.0,
        safety_buffer=portfolio_var_95 - total_cost,
        message="ok",
        metadata={},
    )


def test_feature_overview_and_llp_rows_use_sorted_feature_order() -> None:
    features = [
        _feature("H2: B", cost=50_000.0, llp=0.32, business_value_per_conversion=2.0),
        _feature("H1: A", cost=75_000.0, llp=0.10, business_value_per_conversion=3.0),
    ]
    simulation_results = {
        "H1: A": _sim_result(
            "H1: A",
            np.array([100.0, 120.0, 80.0], dtype=float),
            business_value_per_conversion=3.0,
            development_cost=75_000.0,
        ),
        "H2: B": _sim_result(
            "H2: B",
            np.array([60.0, 65.0, 55.0], dtype=float),
            business_value_per_conversion=2.0,
            development_cost=50_000.0,
        ),
    }

    overview = PortfolioDecisionSupportService.feature_overview_rows(
        features=features,
        simulation_results=simulation_results,
    )
    llp = PortfolioDecisionSupportService.llp_rows(
        features=features,
        simulation_results=simulation_results,
    )

    assert [row[1] for row in overview] == ["H1: A", "H2: B"]
    assert overview[0][0] == "H1"
    assert overview[0][5].endswith("x")
    assert overview[0][-1] == "Low"
    assert overview[1][-1] == "High"
    assert [row[0] for row in llp] == ["H1: A", "H2: B"]


def test_feature_overview_rows_show_inf_roi_for_zero_cost() -> None:
    features = [
        _feature("H1: Free", cost=0.0, llp=0.10, business_value_per_conversion=3.0),
    ]
    simulation_results = {
        "H1: Free": _sim_result(
            "H1: Free",
            np.array([100.0, 120.0, 80.0], dtype=float),
            business_value_per_conversion=3.0,
            development_cost=0.0,
        ),
    }

    overview = PortfolioDecisionSupportService.feature_overview_rows(
        features=features,
        simulation_results=simulation_results,
    )

    assert overview[0][5] == "inf"


def test_feature_overview_rows_include_risk_adjusted_roi_column_order() -> None:
    features = [
        _feature("H1: A", cost=50_000.0, llp=0.10, business_value_per_conversion=3.0),
    ]
    simulation_results = {
        "H1: A": _sim_result(
            "H1: A",
            np.array([100.0, 120.0, 80.0], dtype=float),
            business_value_per_conversion=3.0,
            development_cost=50_000.0,
        ),
    }

    row = PortfolioDecisionSupportService.feature_overview_rows(
        features=features,
        simulation_results=simulation_results,
    )[0]

    assert len(row) == 8
    assert row[5].endswith("x")
    assert row[6].endswith("%")
    assert row[7] == "Low"


def test_feature_overview_rows_risk_adjusted_roi_matches_floor_over_cost() -> None:
    features = [
        _feature("H1: A", cost=40_000.0, llp=0.10, business_value_per_conversion=2.0),
    ]
    simulation_results = {
        "H1: A": _sim_result(
            "H1: A",
            np.array([60_000.0, 80_000.0, 100_000.0], dtype=float),
            business_value_per_conversion=2.0,
            development_cost=40_000.0,
        ),
    }

    row = PortfolioDecisionSupportService.feature_overview_rows(
        features=features,
        simulation_results=simulation_results,
    )[0]
    var_floor = simulation_results["H1: A"].business_value_at_risk_95
    expected_roi = var_floor / 40_000.0

    assert row[5] == f"{expected_roi:.2f}x"


def test_feature_overview_rows_medium_risk_zone_boundary() -> None:
    features = [
        _feature(
            "H2: Medium", cost=50_000.0, llp=0.20, business_value_per_conversion=2.0
        ),
    ]
    simulation_results = {
        "H2: Medium": _sim_result(
            "H2: Medium",
            np.array([200.0, 210.0, 190.0], dtype=float),
            business_value_per_conversion=2.0,
            development_cost=50_000.0,
        ),
    }

    row = PortfolioDecisionSupportService.feature_overview_rows(
        features=features,
        simulation_results=simulation_results,
    )[0]

    assert row[7] == "Medium"


def test_budget_sensitivity_applies_guardrails_before_optimization() -> None:
    features = [
        _feature("A", cost=100.0, llp=0.10),
        _feature("B", cost=200.0, llp=0.10),
    ]
    simulation_results = {
        "A": _sim_result(
            "A",
            np.array([120.0, 200.0, 170.0], dtype=float),
            business_value_per_conversion=1.0,
            development_cost=100.0,
        ),
        "B": _sim_result(
            "B",
            np.array([50.0, 60.0, 70.0], dtype=float),
            business_value_per_conversion=1.0,
            development_cost=200.0,
        ),
    }

    called_budgets: list[float] = []

    def optimize_for_budget(budget: float) -> OptimizationResult:
        called_budgets.append(budget)
        return _optimization_result(
            solver="ilp",
            recommended=("A",),
            total_cost=100.0,
            portfolio_expected=160.0,
            portfolio_var_95=120.0,
            budget=budget,
        )

    result = PortfolioDecisionSupportService.budget_sensitivity(
        levels={"Low": 50.0, "Base": 120.0},
        features=features,
        simulation_results=simulation_results,
        optimize_for_budget=optimize_for_budget,
    )

    assert result["Low"].solver == "not_run"
    assert "cheapest feature" in result["Low"].message
    assert result["Base"].solver == "ilp"
    assert called_budgets == [120.0]


def test_optimize_budget_levels_with_guardrails_returns_skipped_when_not_affordable() -> (
    None
):
    features = [_feature("A", cost=100.0, llp=0.10)]
    simulation_results = {
        "A": _sim_result(
            "A",
            np.array([80.0, 90.0, 100.0], dtype=float),
            business_value_per_conversion=1.0,
            development_cost=100.0,
        )
    }

    results = PortfolioDecisionSupportService.optimize_budget_levels_with_guardrails(
        budget_levels={"Tiny": 50.0},
        features=features,
        simulation_results=simulation_results,
        optimize_for_budget=lambda _budget: _optimization_result(
            solver="ilp",
            recommended=("A",),
            total_cost=100.0,
            portfolio_expected=120.0,
            portfolio_var_95=90.0,
            budget=100.0,
        ),
    )

    assert results["Tiny"].solver == "not_run"
    assert "cheapest feature" in results["Tiny"].message


def test_rank_features_and_negative_score_analysis_return_typed_results() -> None:
    features = [
        _feature("A", cost=100.0, llp=0.10),
        _feature("B", cost=500.0, llp=0.30),
    ]
    simulation_results = {
        "A": _sim_result(
            "A",
            np.array([300.0, 250.0, 280.0], dtype=float),
            business_value_per_conversion=1.0,
            development_cost=100.0,
        ),
        "B": _sim_result(
            "B",
            np.array([200.0, 180.0, 160.0], dtype=float),
            business_value_per_conversion=1.0,
            development_cost=500.0,
        ),
    }

    ranking = PortfolioDecisionSupportService.rank_features(
        features=features,
        simulation_results=simulation_results,
    )

    def solve_candidates(
        candidate_names: tuple[str, ...] | None,
    ) -> dict[str, OptimizationResult]:
        if candidate_names is None:
            return {
                "exact": _optimization_result(
                    solver="exact",
                    recommended=("A", "B"),
                    total_cost=600.0,
                    portfolio_expected=700.0,
                    portfolio_var_95=500.0,
                    budget=700.0,
                ),
                "ilp": _optimization_result(
                    solver="ilp",
                    recommended=("A",),
                    total_cost=100.0,
                    portfolio_expected=300.0,
                    portfolio_var_95=450.0,
                    budget=700.0,
                ),
            }

        return {
            "exact": _optimization_result(
                solver="exact",
                recommended=candidate_names,
                total_cost=100.0,
                portfolio_expected=300.0,
                portfolio_var_95=450.0,
                budget=700.0,
            ),
            "ilp": _optimization_result(
                solver="ilp",
                recommended=candidate_names,
                total_cost=100.0,
                portfolio_expected=300.0,
                portfolio_var_95=450.0,
                budget=700.0,
            ),
        }

    report = PortfolioDecisionSupportService.negative_score_analysis(
        features=features,
        simulation_results=simulation_results,
        solve_candidates=solve_candidates,
    )

    assert ranking[0].feature == "A"
    assert report.positive_features == ("A",)
    assert report.negative_features == ("B",)
    assert len(report.comparisons) == 4
    assert report.gap_exact_minus_ilp == pytest.approx(50.0)


def test_rank_features_supports_multiple_strategies() -> None:
    features = [
        _feature("A", cost=100.0, llp=0.10),
        _feature("B", cost=120.0, llp=0.30),
    ]
    simulation_results = {
        "A": _sim_result(
            "A",
            np.array([95.0, 100.0, 105.0], dtype=float),
            business_value_per_conversion=1.0,
            development_cost=100.0,
        ),
        "B": _sim_result(
            "B",
            np.array([20.0, 90.0, 200.0], dtype=float),
            business_value_per_conversion=1.0,
            development_cost=120.0,
        ),
    }

    by_var_floor = PortfolioDecisionSupportService.rank_features(
        features=features,
        simulation_results=simulation_results,
        strategy="var_floor",
    )
    by_risk_ratio = PortfolioDecisionSupportService.rank_features(
        features=features,
        simulation_results=simulation_results,
        strategy="risk_ratio",
    )
    by_rorac = PortfolioDecisionSupportService.rank_features(
        features=features,
        simulation_results=simulation_results,
        strategy="rorac",
    )
    by_risk_adjusted_roi = PortfolioDecisionSupportService.rank_features(
        features=features,
        simulation_results=simulation_results,
        strategy="risk_adjusted_roi",
    )

    assert by_var_floor[0].feature == "A"
    assert by_risk_ratio[0].feature == "A"
    assert by_rorac[0].feature == "A"
    assert by_risk_adjusted_roi[0].feature == "A"
    assert (
        by_var_floor[0].var_95_business_value >= by_var_floor[1].var_95_business_value
    )
    assert by_risk_ratio[0].risk_ratio <= by_risk_ratio[1].risk_ratio
    assert by_rorac[0].rorac >= by_rorac[1].rorac
    assert (
        by_risk_adjusted_roi[0].risk_adjusted_roi
        >= by_risk_adjusted_roi[1].risk_adjusted_roi
    )


def test_rank_features_invalid_strategy_raises() -> None:
    features = [_feature("A", cost=100.0, llp=0.10)]
    simulation_results = {
        "A": _sim_result(
            "A",
            np.array([100.0, 110.0, 120.0], dtype=float),
            business_value_per_conversion=1.0,
            development_cost=100.0,
        )
    }

    with pytest.raises(ValueError, match="Unknown ranking strategy"):
        PortfolioDecisionSupportService.rank_features(
            features=features,
            simulation_results=simulation_results,
            strategy="unknown",
        )


def test_budget_risk_path_and_risk_contribution_rows_build_outputs() -> None:
    def optimize_for_budget(budget: float) -> OptimizationResult:
        if budget < 100.0:
            return _optimization_result(
                solver="ilp",
                recommended=(),
                total_cost=0.0,
                portfolio_expected=0.0,
                portfolio_var_95=0.0,
                budget=budget,
            )
        return _optimization_result(
            solver="ilp",
            recommended=("A",),
            total_cost=100.0,
            portfolio_expected=180.0,
            portfolio_var_95=120.0,
            budget=budget,
        )

    def analyze_delivery_risk(
        result: OptimizationResult, **_: object
    ) -> dict[str, float]:
        return {
            "market_var_95": result.portfolio_var_95,
            "simulated_var_95": result.portfolio_var_95 - 10.0,
            "shocked_var_95": result.portfolio_var_95 - 20.0,
            "shocked_safety_buffer": (result.portfolio_var_95 - 20.0)
            - result.total_cost,
        }

    path = PortfolioDecisionSupportService.budget_risk_path(
        levels={"Low": 50.0, "Base": 150.0},
        optimize_for_budget=optimize_for_budget,
        analyze_delivery_risk=analyze_delivery_risk,
        seed=42,
    )

    features = {
        "A": _feature("A", cost=100.0, llp=0.10, business_value_per_conversion=2.0),
        "B": _feature("B", cost=120.0, llp=0.20, business_value_per_conversion=1.0),
    }
    simulation_results = {
        "A": _sim_result(
            "A",
            np.array([100.0, 120.0, 80.0], dtype=float),
            business_value_per_conversion=2.0,
            development_cost=100.0,
        ),
        "B": _sim_result(
            "B",
            np.array([50.0, 60.0, 40.0], dtype=float),
            business_value_per_conversion=1.0,
            development_cost=120.0,
        ),
    }
    portfolio_scenarios = np.array([220.0, 260.0, 200.0], dtype=float)

    rows = PortfolioDecisionSupportService.risk_contribution_rows(
        names=("A", "B"),
        feature_by_name=features,
        simulation_results=simulation_results,
        portfolio_scenarios=portfolio_scenarios,
    )

    assert [row.label for row in path] == ["Low", "Base"]
    assert path[0].risk_class == "No selection"
    assert path[1].risk_class in {"Low", "Medium", "High"}
    assert len(rows) == 2
    assert rows[0][5] >= rows[1][5]
