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

"""Portfolio view assembly service for facade-level outputs."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

import numpy as np
from scipy import stats

from fhs.core.model.value_objects import (
    BudgetFrontierRow,
    ConcentrationResult,
    OptimizationResult,
    PortfolioSnapshot,
)
from fhs.core.services.risk import RiskCalculator


class PortfolioViewService:
    """Build high-level portfolio views from precomputed inputs."""

    @staticmethod
    def _delta_pct(value: float, baseline: float) -> float:
        if baseline <= 0:
            return 0.0  # pragma: no cover - defensive
        return ((value / baseline) - 1.0) * 100.0

    @classmethod
    def _scenario_view_row(
        cls,
        *,
        label: str,
        stressed: np.ndarray,
        baseline: PortfolioSnapshot,
    ) -> dict[str, float | str]:
        expected = float(np.mean(stressed)) if len(stressed) > 0 else 0.0
        var_95 = float(np.percentile(stressed, 5)) if len(stressed) > 0 else 0.0
        return {
            "name": label,
            "expected": expected,
            "var_95": var_95,
            "expected_delta_pct": cls._delta_pct(expected, baseline.expected),
            "var_delta_pct": cls._delta_pct(var_95, baseline.var_95),
        }

    @staticmethod
    def portfolio_snapshot_from_scenarios(
        scenarios: np.ndarray,
        *,
        investment: float = 0.0,
    ) -> PortfolioSnapshot:
        """Build a PortfolioSnapshot from aggregated portfolio scenarios."""
        if len(scenarios) == 0:
            return PortfolioSnapshot(  # pragma: no cover - defensive
                expected=0.0,
                var_95=0.0,
                cvar_95=0.0,
                std_dev=0.0,
                investment=float(investment),
            )

        var_95 = float(np.percentile(scenarios, 5))
        tail = scenarios[scenarios <= var_95]
        return PortfolioSnapshot(
            expected=float(np.mean(scenarios)),
            var_95=var_95,
            cvar_95=float(np.mean(tail)) if len(tail) > 0 else var_95,
            std_dev=float(np.std(scenarios)),
            investment=float(investment),
        )

    @staticmethod
    def concentration_from_expected_business_values(
        expected_business_values: Mapping[str, float],
    ) -> ConcentrationResult:
        """Build HHI concentration summary from expected feature business values."""
        total = float(sum(float(v) for v in expected_business_values.values()))
        if total <= 0.0:
            return ConcentrationResult(  # pragma: no cover - defensive
                hhi=0.0,
                shares={},
                verdict="Low concentration",
            )

        shares = {
            str(name): float(value) / total
            for name, value in expected_business_values.items()
        }
        hhi = float(RiskCalculator.calculate_hhi(shares))
        if hhi >= 0.25:
            verdict = "High concentration"
        elif hhi >= 0.15:  # pragma: no cover - defensive
            verdict = "Moderate concentration"  # pragma: no cover - defensive
        else:  # pragma: no cover - defensive
            verdict = "Low concentration"  # pragma: no cover - defensive
        return ConcentrationResult(
            hhi=hhi,
            shares=shares,
            verdict=verdict,
        )

    @staticmethod
    def budget_frontier_rows(
        *,
        budgets: Iterable[float],
        optimize_for_budget: Callable[[float], OptimizationResult],
    ) -> list[BudgetFrontierRow]:
        """Build budget frontier rows by evaluating sorted budget levels."""
        rows: list[BudgetFrontierRow] = []
        for budget in sorted(float(b) for b in budgets):
            result = optimize_for_budget(budget)
            rows.append(
                BudgetFrontierRow(
                    budget=budget,
                    selected_count=len(result.recommended_features),
                    expected=result.portfolio_expected,
                    var_95=result.portfolio_var_95,
                    cost=result.total_cost,
                    budget_remaining=result.budget_remaining,
                    roi=result.portfolio_roi,
                )
            )
        return rows

    @staticmethod
    def optimization_result_from_solver_result(
        solver_result: Any,
    ) -> OptimizationResult:
        """Normalize solver output into typed OptimizationResult."""
        total_cost = float(solver_result.total_cost)
        expected = float(solver_result.portfolio_expected)
        var_95 = float(solver_result.portfolio_var_95)
        budget_value = float(solver_result.budget)
        budget_remaining = float(solver_result.budget_remaining)
        metadata = (
            {str(key): value for key, value in solver_result.metadata.items()}
            if isinstance(solver_result.metadata, dict)
            else {"raw": solver_result.metadata}
        )
        roi = (expected - total_cost) / total_cost if total_cost > 0 else 0.0

        return OptimizationResult(
            recommended_features=tuple(
                str(name) for name in solver_result.recommended_features
            ),
            total_cost=total_cost,
            portfolio_expected=expected,
            portfolio_var_95=var_95,
            portfolio_cvar_95=float(solver_result.portfolio_cvar_95),
            portfolio_std_dev=float(solver_result.portfolio_std_dev),
            budget=budget_value,
            budget_remaining=budget_remaining,
            computation_time_sec=float(solver_result.computation_time_sec),
            combinations_evaluated=int(solver_result.combinations_evaluated),
            solver=str(solver_result.solver),
            strategy=str(solver_result.strategy),
            portfolio_roi=roi,
            roi=roi,
            safety_buffer=var_95 - total_cost,
            message=str(solver_result.message),
            metadata=metadata,
        )

    @staticmethod
    def optimize_portfolio(
        *,
        optimizer: Any,
        solver: str,
        budget: float,
        strategy: str,
        sum_portfolio_scenarios_fn: Callable[[dict[str, Any]], np.ndarray],
        seed: int,
        discount_rate: float = 0.08,
        k: int = 20,
        alpha: float = 0.95,
        n_scenarios: int = 300,
    ) -> OptimizationResult:
        """Run selected optimizer solver and return typed OptimizationResult."""
        if solver == "exact":
            solver_result = optimizer.optimize_exact(
                budget=budget,
                strategy=strategy,
                sum_portfolio_scenarios_fn=sum_portfolio_scenarios_fn,
                discount_rate=discount_rate,
            )
        elif solver == "ilp":
            solver_result = optimizer.optimize_ilp(
                budget=budget,
                strategy=strategy,
                sum_portfolio_scenarios_fn=sum_portfolio_scenarios_fn,
                discount_rate=discount_rate,
            )
        elif solver == "greedy":
            solver_result = optimizer.optimize_greedy(
                budget=budget,
                strategy=strategy,
                sum_portfolio_scenarios_fn=sum_portfolio_scenarios_fn,
                k=k,
                seed=seed,
                discount_rate=discount_rate,
            )
        elif solver == "cvar_milp":
            solver_result = optimizer.optimize_cvar(
                budget=budget,
                alpha=alpha,
                n_scenarios=n_scenarios,
                sum_portfolio_scenarios_fn=sum_portfolio_scenarios_fn,
            )
        else:
            raise ValueError(  # pragma: no cover - defensive
                "Unknown solver "
                f"'{solver}'. Use 'exact', 'ilp', 'greedy', or 'cvar_milp'."
            )

        return PortfolioViewService.optimization_result_from_solver_result(
            solver_result
        )

    @staticmethod
    def stress_scenarios_view(
        *,
        resolved: Sequence[str],
        baseline: PortfolioSnapshot,
        components: Mapping[str, np.ndarray],
        top_feature: str | None,
        is_high_delivery_risk: Callable[[str], bool],
    ) -> dict[str, Any]:
        """Build stress-scenario table from component business value arrays."""
        if not resolved:
            return {
                "baseline": baseline,
                "scenarios": [],
            }  # pragma: no cover - defensive

        baseline_arr = (
            np.sum(list(components.values()), axis=0)
            if components
            else np.array([], dtype=float)
        )

        scenario_defs = [
            (
                "Market pullback",
                dict.fromkeys(resolved, 0.7),
            ),
            (
                "Top feature delay",
                {
                    name: (
                        0.25 if top_feature is not None and name == top_feature else 1.0
                    )
                    for name in resolved
                },
            ),
            (
                "Execution pressure",
                {
                    name: (0.60 if is_high_delivery_risk(name) else 0.85)
                    for name in resolved
                },
            ),
        ]

        scenarios: list[dict[str, float | str]] = []
        for label, multipliers in scenario_defs:
            stressed = np.zeros(len(baseline_arr), dtype=float)
            for name in resolved:
                stressed += components[name] * multipliers[name]

            scenarios.append(
                PortfolioViewService._scenario_view_row(
                    label=label,
                    stressed=stressed,
                    baseline=baseline,
                )
            )

        return {
            "baseline": baseline,
            "scenarios": scenarios,
        }

    @staticmethod
    def dependency_correlation_view(
        *,
        labels: Sequence[str],
        dependency_matrix: np.ndarray,
        business_value_arrays: np.ndarray,
    ) -> dict[str, Any]:
        """Build configured-vs-empirical correlation view."""
        if not labels:
            empty = np.array([[]], dtype=float)
            return {
                "labels": [],
                "dependency_matrix": empty,
                "empirical_matrix": empty,
                "spearman_matrix": empty,
                "average_corr": 0.0,
            }

        if len(labels) == 1:
            empirical = np.array([[1.0]], dtype=float)  # pragma: no cover - defensive
            spear = np.array([[1.0]], dtype=float)  # pragma: no cover - defensive
            average_corr = 0.0  # pragma: no cover - defensive
        else:
            empirical = np.corrcoef(business_value_arrays, rowvar=False)
            spear = np.asarray(
                stats.spearmanr(business_value_arrays).statistic, dtype=float
            )
            average_corr = float(np.mean(empirical[~np.eye(len(labels), dtype=bool)]))

        return {
            "labels": list(labels),
            "dependency_matrix": dependency_matrix,
            "empirical_matrix": empirical,
            "spearman_matrix": spear,
            "average_corr": average_corr,
        }
