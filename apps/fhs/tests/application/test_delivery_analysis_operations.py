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

"""Tests for DeliveryAnalysisOperations static methods."""

from __future__ import annotations

import numpy as np
import pytest

from fhs.application.delivery_analysis_operations import DeliveryAnalysisOperations
from fhs.core.model import DeliverySimulationResult, Feature

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _feature(name: str, cost: float, weeks: float = 8.0) -> Feature:
    return Feature(
        name=name,
        expected_users=5_000,
        conversion_rate=0.10,
        uncertainty=0.20,
        business_value_per_conversion=20.0,
        development_cost=cost,
        annual_growth_rate=0.05,
        likelihood_of_non_delivery=0.05,
        development_weeks=weeks,
    )


def _delivery_result(
    name: str,
    planned_sprints: int,
    actual_cost: list[float],
    actual_sprints: list[int] | None = None,
    cancelled: list[bool] | None = None,
) -> DeliverySimulationResult:
    n = len(actual_cost)
    return DeliverySimulationResult(
        feature_name=name,
        planned_sprints=planned_sprints,
        actual_sprints=np.array(
            actual_sprints if actual_sprints is not None else [planned_sprints] * n
        ),
        actual_cost=np.array(actual_cost, dtype=float),
        cancelled=np.array(cancelled if cancelled is not None else [False] * n),
        business_value_after_risk=np.array([50_000.0] * n),
    )


# ---------------------------------------------------------------------------
# budget_fit_rows
# ---------------------------------------------------------------------------


class TestBudgetFitRows:
    def test_returns_one_row_per_feature(self) -> None:
        features = [_feature("H1: Alpha", 40_000), _feature("H2: Beta", 60_000)]
        results = {
            "H1: Alpha": _delivery_result("H1: Alpha", 4, [40_000, 44_000, 48_000]),
            "H2: Beta": _delivery_result("H2: Beta", 6, [60_000, 66_000, 70_000]),
        }
        rows = DeliveryAnalysisOperations.budget_fit_rows(features, results)
        assert len(rows) == 2

    def test_sorted_by_pressure_ascending(self) -> None:
        # Alpha has lower CVaR → lower pressure → ranked first
        features = [_feature("H1: Alpha", 40_000), _feature("H2: Beta", 40_000)]
        results = {
            "H1: Alpha": _delivery_result(
                "H1: Alpha", 4, [40_000] * 100 + [42_000] * 900
            ),
            "H2: Beta": _delivery_result(
                "H2: Beta", 4, [40_000] * 100 + [50_000] * 900
            ),
        }
        rows = DeliveryAnalysisOperations.budget_fit_rows(features, results)
        # Priority column is index 0; "1" means first/lowest pressure
        assert rows[0][0] == "1"
        assert "Alpha" in rows[0][1]

    def test_feature_without_result_is_skipped(self) -> None:
        features = [_feature("H1: Alpha", 40_000), _feature("H2: Beta", 60_000)]
        results = {
            "H1: Alpha": _delivery_result("H1: Alpha", 4, [40_000, 44_000]),
        }
        rows = DeliveryAnalysisOperations.budget_fit_rows(features, results)
        assert len(rows) == 1

    def test_row_format(self) -> None:
        features = [_feature("H1: Alpha", 40_000)]
        results = {
            "H1: Alpha": _delivery_result("H1: Alpha", 4, [40_000] * 1000),
        }
        rows = DeliveryAnalysisOperations.budget_fit_rows(features, results)
        priority, name, planned, cvar, pressure = rows[0]
        assert priority == "1"
        assert name == "Alpha"
        assert "40,000" in planned
        assert "EUR" in cvar
        assert "%" in pressure

    def test_prefix_stripped_from_name(self) -> None:
        features = [_feature("H3: Gamma Feature", 30_000)]
        results = {
            "H3: Gamma Feature": _delivery_result(
                "H3: Gamma Feature", 3, [30_000] * 10
            ),
        }
        rows = DeliveryAnalysisOperations.budget_fit_rows(features, results)
        assert rows[0][1] == "Gamma Feature"


# ---------------------------------------------------------------------------
# budget_fit_summary
# ---------------------------------------------------------------------------


class TestBudgetFitSummary:
    def test_returns_required_keys(self) -> None:
        features = [_feature("H1: Alpha", 40_000)]
        results = {
            "H1: Alpha": _delivery_result(
                "H1: Alpha", 4, [40_000] * 100 + [50_000] * 900
            ),
        }
        summary = DeliveryAnalysisOperations.budget_fit_summary(
            features, results, 100_000.0
        )
        assert set(summary) >= {"budget", "planned_total", "cvar_total", "budget_gap"}

    def test_planned_total_sums_development_cost(self) -> None:
        features = [_feature("H1: Alpha", 40_000), _feature("H2: Beta", 60_000)]
        results = {
            "H1: Alpha": _delivery_result("H1: Alpha", 4, [40_000] * 10),
            "H2: Beta": _delivery_result("H2: Beta", 6, [60_000] * 10),
        }
        summary = DeliveryAnalysisOperations.budget_fit_summary(
            features, results, 150_000.0
        )
        assert summary["planned_total"] == pytest.approx(100_000.0)

    def test_budget_gap_equals_cvar_minus_budget(self) -> None:
        features = [_feature("H1: Alpha", 40_000)]
        results = {
            "H1: Alpha": _delivery_result("H1: Alpha", 4, [50_000] * 1000),
        }
        summary = DeliveryAnalysisOperations.budget_fit_summary(
            features, results, 40_000.0
        )
        assert summary["budget_gap"] == pytest.approx(
            summary["cvar_total"] - summary["budget"]
        )

    def test_feature_without_result_excluded_from_totals(self) -> None:
        features = [_feature("H1: Alpha", 40_000), _feature("H2: Beta", 60_000)]
        results = {
            "H1: Alpha": _delivery_result("H1: Alpha", 4, [40_000] * 10),
        }
        summary = DeliveryAnalysisOperations.budget_fit_summary(
            features, results, 100_000.0
        )
        assert summary["planned_total"] == pytest.approx(40_000.0)


# ---------------------------------------------------------------------------
# delivery_cost_risk_rows
# ---------------------------------------------------------------------------


class TestDeliveryCostRiskRows:
    def test_returns_one_row_per_feature_with_result(self) -> None:
        features = [_feature("H1: Alpha", 40_000), _feature("H2: Beta", 60_000)]
        results = {
            "H1: Alpha": _delivery_result("H1: Alpha", 4, [40_000, 44_000]),
        }
        rows = DeliveryAnalysisOperations.delivery_cost_risk_rows(features, results)
        assert len(rows) == 1

    def test_row_has_seven_columns(self) -> None:
        features = [_feature("H1: Alpha", 40_000)]
        results = {
            "H1: Alpha": _delivery_result(
                "H1: Alpha", 4, [40_000] * 100 + [50_000] * 900
            ),
        }
        rows = DeliveryAnalysisOperations.delivery_cost_risk_rows(features, results)
        assert len(rows[0]) == 7

    def test_uplift_positive_when_expected_exceeds_planned(self) -> None:
        features = [_feature("H1: Alpha", 40_000)]
        # All scenarios cost more than planned → positive uplift
        results = {
            "H1: Alpha": _delivery_result("H1: Alpha", 4, [48_000] * 1000),
        }
        rows = DeliveryAnalysisOperations.delivery_cost_risk_rows(features, results)
        uplift_str = rows[0][5]  # index 5 = "Uplift vs plan"
        assert "+" in uplift_str

    def test_prefix_stripped_from_feature_name(self) -> None:
        features = [_feature("H2: My Feature", 30_000)]
        results = {
            "H2: My Feature": _delivery_result("H2: My Feature", 3, [30_000] * 10),
        }
        rows = DeliveryAnalysisOperations.delivery_cost_risk_rows(features, results)
        assert rows[0][0] == "My Feature"

    def test_cancelled_percentage_shown(self) -> None:
        cancelled = [False] * 800 + [True] * 200
        features = [_feature("H1: Alpha", 40_000)]
        results = {
            "H1: Alpha": _delivery_result(
                "H1: Alpha", 4, [40_000] * 1000, cancelled=cancelled
            ),
        }
        rows = DeliveryAnalysisOperations.delivery_cost_risk_rows(features, results)
        assert "20" in rows[0][6]  # 20% cancellation


# ---------------------------------------------------------------------------
# min_cost_cvar_selection
# ---------------------------------------------------------------------------


class TestMinCostCvarSelection:
    def test_empty_when_budget_zero(self) -> None:
        features = [_feature("H1: Alpha", 40_000)]
        results = {
            "H1: Alpha": _delivery_result("H1: Alpha", 4, [40_000] * 100),
        }
        result = DeliveryAnalysisOperations.min_cost_cvar_selection(
            features, results, budget=0.0
        )
        assert result == {}

    def test_empty_when_no_feature_fits_budget(self) -> None:
        features = [_feature("H1: Alpha", 100_000)]
        results = {
            "H1: Alpha": _delivery_result("H1: Alpha", 10, [100_000] * 100),
        }
        result = DeliveryAnalysisOperations.min_cost_cvar_selection(
            features, results, budget=50_000.0
        )
        assert result == {}

    def test_selects_single_feature_when_only_one_fits(self) -> None:
        features = [_feature("H1: Alpha", 40_000), _feature("H2: Beta", 90_000)]
        results = {
            "H1: Alpha": _delivery_result("H1: Alpha", 4, [40_000] * 100),
            "H2: Beta": _delivery_result("H2: Beta", 9, [90_000] * 100),
        }
        result = DeliveryAnalysisOperations.min_cost_cvar_selection(
            features, results, budget=50_000.0
        )
        assert result["selected"] == ["H1: Alpha"]

    def test_selects_all_when_all_fit(self) -> None:
        features = [_feature("H1: Alpha", 30_000), _feature("H2: Beta", 40_000)]
        results = {
            "H1: Alpha": _delivery_result("H1: Alpha", 3, [30_000] * 100),
            "H2: Beta": _delivery_result("H2: Beta", 4, [40_000] * 100),
        }
        result = DeliveryAnalysisOperations.min_cost_cvar_selection(
            features, results, budget=100_000.0
        )
        assert set(result["selected"]) == {"H1: Alpha", "H2: Beta"}

    def test_maximises_feature_count(self) -> None:
        # Budget fits either [Alpha+Beta] (2 features, €70k) or [Gamma] (1 feature, €80k)
        # Must prefer the 2-feature combination
        features = [
            _feature("H1: Alpha", 30_000),
            _feature("H2: Beta", 40_000),
            _feature("H3: Gamma", 80_000),
        ]
        results = {
            "H1: Alpha": _delivery_result("H1: Alpha", 3, [30_000] * 1000),
            "H2: Beta": _delivery_result("H2: Beta", 4, [40_000] * 1000),
            "H3: Gamma": _delivery_result("H3: Gamma", 8, [80_000] * 1000),
        }
        result = DeliveryAnalysisOperations.min_cost_cvar_selection(
            features, results, budget=90_000.0
        )
        assert len(result["selected"]) == 2
        assert set(result["selected"]) == {"H1: Alpha", "H2: Beta"}

    def test_normalised_pressure_as_tiebreaker(self) -> None:
        # Budget = 110k. Two 2-feature combinations possible:
        #   Alpha(50k) + Beta(60k) = 110k, both have high CVaR overrun
        #   Alpha(50k) + Gamma(55k) = 105k, lower relative CVaR pressure
        # normalised pressure = CVaR/planned - 1; Gamma combination wins
        n = 10_000
        rng = np.random.default_rng(0)

        # Beta: high spread → high CVaR relative to its cost
        beta_costs = np.clip(rng.normal(60_000, 15_000, n), 60_000, 120_000).tolist()
        # Gamma: tight distribution → low CVaR relative to its cost
        gamma_costs = np.clip(rng.normal(55_000, 2_000, n), 55_000, 70_000).tolist()

        features = [
            _feature("H1: Alpha", 50_000),
            _feature("H2: Beta", 60_000),
            _feature("H3: Gamma", 55_000),
        ]
        results = {
            "H1: Alpha": _delivery_result("H1: Alpha", 5, [50_000] * n),
            "H2: Beta": _delivery_result("H2: Beta", 6, beta_costs),
            "H3: Gamma": _delivery_result("H3: Gamma", 5, gamma_costs),
        }
        result = DeliveryAnalysisOperations.min_cost_cvar_selection(
            features, results, budget=110_000.0
        )
        assert len(result["selected"]) == 2
        assert "H3: Gamma" in result["selected"]

    def test_result_keys_present(self) -> None:
        features = [_feature("H1: Alpha", 40_000)]
        results = {
            "H1: Alpha": _delivery_result(
                "H1: Alpha", 4, [40_000] * 100 + [50_000] * 900
            ),
        }
        result = DeliveryAnalysisOperations.min_cost_cvar_selection(
            features, results, budget=50_000.0
        )
        assert set(result) >= {
            "selected",
            "total_planned_cost",
            "budget_remaining",
            "budget_pressure",
            "expected_cost",
            "portfolio_car",
            "portfolio_cvar",
        }

    def test_budget_pressure_uses_planned_cost_as_denominator(self) -> None:
        # pressure = CVaR / total_planned_cost - 1, NOT planned / scenario_budget - 1
        features = [_feature("H1: Alpha", 40_000)]
        # All costs exactly at plan → CVaR ≈ planned → pressure ≈ 0
        results = {
            "H1: Alpha": _delivery_result("H1: Alpha", 4, [40_000] * 1000),
        }
        result = DeliveryAnalysisOperations.min_cost_cvar_selection(
            features, results, budget=200_000.0
        )
        assert result["budget_pressure"] == pytest.approx(0.0, abs=0.01)

    def test_budget_remaining_equals_budget_minus_planned(self) -> None:
        features = [_feature("H1: Alpha", 40_000)]
        results = {
            "H1: Alpha": _delivery_result("H1: Alpha", 4, [40_000] * 100),
        }
        result = DeliveryAnalysisOperations.min_cost_cvar_selection(
            features, results, budget=100_000.0
        )
        assert result["budget_remaining"] == pytest.approx(60_000.0)

    def test_portfolio_cvar_ge_portfolio_car(self) -> None:
        features = [_feature("H1: Alpha", 40_000)]
        results = {
            "H1: Alpha": _delivery_result(
                "H1: Alpha", 4, [40_000] * 900 + [60_000] * 100
            ),
        }
        result = DeliveryAnalysisOperations.min_cost_cvar_selection(
            features, results, budget=100_000.0
        )
        assert result["portfolio_cvar"] >= result["portfolio_car"]


# ---------------------------------------------------------------------------
# cost_risk_combination_rows
# ---------------------------------------------------------------------------


class TestCostRiskCombinationRows:
    def test_returns_all_budget_feasible_combinations(self) -> None:
        features = [
            _feature("H1: Alpha", 75_000),
            _feature("H2: Beta", 45_000),
            _feature("H3: Gamma", 45_000),
        ]
        n = 200
        results = {
            "H1: Alpha": _delivery_result("H1: Alpha", 3, [100_000] * n),
            "H2: Beta": _delivery_result("H2: Beta", 3, [70_000] * n),
            "H3: Gamma": _delivery_result("H3: Gamma", 2, [80_000] * n),
        }

        rows = DeliveryAnalysisOperations.cost_risk_combination_rows(
            features,
            results,
            budget=155_000.0,
        )

        # 3 singles + 3 pairs fit; triple is infeasible (165k > 155k)
        assert len(rows) == 6

    def test_marks_selected_combination(self) -> None:
        features = [
            _feature("H1: Alpha", 75_000),
            _feature("H2: Beta", 45_000),
            _feature("H3: Gamma", 45_000),
        ]
        n = 2_000
        # Beta has same relative pressure as Alpha; Gamma has worse individual
        # pressure but improves the portfolio tail with Alpha.
        results = {
            "H1: Alpha": _delivery_result("H1: Alpha", 3, [75_000, 135_000] * n),
            "H2: Beta": _delivery_result("H2: Beta", 3, [45_000, 81_000] * n),
            "H3: Gamma": _delivery_result("H3: Gamma", 2, [45_000, 93_000] * n),
        }

        rows = DeliveryAnalysisOperations.cost_risk_combination_rows(
            features,
            results,
            budget=155_000.0,
        )

        selection = DeliveryAnalysisOperations.min_cost_cvar_selection(
            features,
            results,
            budget=155_000.0,
        )
        expected_name_set = {
            name.split(": ", 1)[-1] for name in selection.get("selected", [])
        }

        selected_rows = [row for row in rows if row[1] == "Yes"]
        assert len(selected_rows) == 1
        selected_name_set = {
            name.strip() for name in selected_rows[0][3].split(",") if name.strip()
        }
        assert selected_name_set == expected_name_set
