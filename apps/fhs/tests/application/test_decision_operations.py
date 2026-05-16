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

"""Tests for DecisionOperations — coverage for missing branches."""

from __future__ import annotations

import pytest

from fhs.application.advanced_portfolio_service import AdvancedPortfolioService
from fhs.application.decision_operations import DecisionOperations
from fhs.core.model import Feature, OptimizationResult

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def service() -> AdvancedPortfolioService:
    features = [
        Feature(
            name="H1: UI",
            expected_users=50_000,
            conversion_rate=0.20,
            uncertainty=0.20,
            business_value_per_conversion=5.0,
            development_cost=50_000.0,
            annual_operating_cost=10_000.0,
            annual_growth_rate=0.05,
            development_weeks=6,
        ),
        Feature(
            name="H2: API",
            expected_users=30_000,
            conversion_rate=0.30,
            uncertainty=0.25,
            business_value_per_conversion=4.0,
            development_cost=40_000.0,
            annual_operating_cost=8_000.0,
            annual_growth_rate=0.05,
            development_weeks=4,
        ),
    ]
    return AdvancedPortfolioService(
        features,
        budget=100_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=1_000,
    )


def _opt_result(
    *,
    solver: str = "ilp",
    recommended: tuple[str, ...] = (),
    total_cost: float = 0.0,
    portfolio_expected: float = 0.0,
    portfolio_var_95: float = 0.0,
    budget: float = 100_000.0,
    message: str | None = None,
    combinations_evaluated: int = 1,
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
        combinations_evaluated=combinations_evaluated,
        solver=solver,
        strategy="var_floor",
        roi=0.0,
        message=message or "",
        safety_buffer=0.0,
        portfolio_roi=0.0,
        metadata={},
    )


# ---------------------------------------------------------------------------
# Line 429 — _result_field with dict input (defensive branch)
# ---------------------------------------------------------------------------


class TestResultFieldWithDict:
    def test_result_field_reads_key_from_dict(self) -> None:
        result = DecisionOperations._result_field(
            {"recommended_features": ("H1: UI",)}, "recommended_features"
        )
        assert result == ("H1: UI",)

    def test_result_field_returns_none_for_missing_key(self) -> None:
        result = DecisionOperations._result_field({}, "missing_key")
        assert result is None


# ---------------------------------------------------------------------------
# Lines 289-301 — stress_scenarios when portfolio_snapshot_fn is None
# ---------------------------------------------------------------------------


class TestStressScenariosWithoutSnapshotFn:
    def test_stress_scenarios_computes_baseline_from_arrays(
        self, service: AdvancedPortfolioService
    ) -> None:
        result = service.decisions.stress_scenarios(portfolio_snapshot_fn=None)
        assert "baseline" in result
        assert result["baseline"] is not None


# ---------------------------------------------------------------------------
# Lines 116-123 — negative_score_analysis when candidate_names is None
# (baseline comparison uses full feature set)
# ---------------------------------------------------------------------------


class TestNegativeScoreAnalysisFullFeatureSet:
    def test_negative_score_analysis_runs_with_baseline_on_full_set(
        self, service: AdvancedPortfolioService
    ) -> None:
        report = service.decisions.negative_score_analysis(
            spawn_subset_fn=lambda features, budget: AdvancedPortfolioService(
                features,
                budget=budget,
                discount_rate=0.08,
                seed=42,
                scenarios=1_000,
            ),
            optimize_fn=lambda **kwargs: service.optimize(**kwargs),
        )
        assert report is not None


# ---------------------------------------------------------------------------
# Line 517 — negative_score_comparison_rows when result is None
# ---------------------------------------------------------------------------


class TestNegativeScoreComparisonRowsSkipsNone:
    def test_skips_none_result_in_results_all(
        self, service: AdvancedPortfolioService
    ) -> None:
        good_result = _opt_result(
            solver="exact",
            recommended=("H1: UI",),
            total_cost=50_000.0,
            portfolio_expected=80_000.0,
            portfolio_var_95=40_000.0,
            budget=100_000.0,
        )
        rows = service.decisions.negative_score_comparison_rows(
            results_all={"exact": good_result, "ilp": None},
            results_positive={"exact": good_result, "ilp": None},
        )
        # Only one non-None entry per label group → 2 rows (All + Positive with exact)
        assert len(rows) == 2


# ---------------------------------------------------------------------------
# Line 584 — selected_portfolio_rows when feature name not found
# ---------------------------------------------------------------------------


class TestSelectedPortfolioRowsSkipsUnknown:
    def test_skips_unknown_feature_name(
        self, service: AdvancedPortfolioService
    ) -> None:
        rows = service.decisions.selected_portfolio_rows(["Unknown Feature"])
        assert rows == []


# ---------------------------------------------------------------------------
# Lines 708-710 — decision_table_rows when solver == "not_run"
# Lines 718-720 — decision_table_rows when no features selected
# ---------------------------------------------------------------------------


class TestDecisionTableRowsBranches:
    def test_not_run_solver_produces_not_optimized_note(self) -> None:
        not_run = _opt_result(
            solver="not_run",
            budget=1.0,
            message="Budget too low",
        )
        rows = DecisionOperations.decision_table_rows(
            {"Tiny Budget": 1.0}, {"Tiny Budget": not_run}
        )
        assert len(rows) == 1
        row = rows[0]
        # selection_note is column index 3
        assert "Not optimized" in row[3] or "Budget too low" in row[3]

    def test_empty_selection_produces_no_build_selected_note(self) -> None:
        empty = _opt_result(
            solver="ilp",
            recommended=(),
            combinations_evaluated=5,
            budget=100_000.0,
        )
        rows = DecisionOperations.decision_table_rows(
            {"Some Budget": 100_000.0}, {"Some Budget": empty}
        )
        assert len(rows) == 1
        assert "No build selected" in rows[0][3]


# ---------------------------------------------------------------------------
# Lines 818-859, 872-890 — npv_feature_comparison_rows
# Lines 906-955 — npv_decision_table_rows
# ---------------------------------------------------------------------------


class TestNpvMethods:
    def test_npv_feature_comparison_rows_returns_one_row_per_feature(
        self, service: AdvancedPortfolioService
    ) -> None:
        rows = service.decisions.npv_feature_comparison_rows(discount_rate=0.08)
        assert len(rows) == 2
        assert all(len(row) == 5 for row in rows)

    def test_npv_decision_table_rows_returns_two_rows_per_budget_level(
        self, service: AdvancedPortfolioService
    ) -> None:
        opt = service.optimize(solver="ilp", budget=100_000.0)
        rows = service.decisions.npv_decision_table_rows(
            budget_levels={"100%": 100_000.0},
            ilp_year1={"100%": opt},
            ilp_3year={"100%": opt},
            discount_rate=0.08,
        )
        # 2 horizon rows per budget level (3 Years + Year 1)
        assert len(rows) == 2
        assert all(len(row) == 6 for row in rows)
