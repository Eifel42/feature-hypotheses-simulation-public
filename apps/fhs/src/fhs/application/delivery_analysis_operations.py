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

"""Development risk, sprint overruns, and profitability analysis operations."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import numpy as np

from fhs.application.portfolio_context import PortfolioContext
from fhs.core.model import (
    DeliveryRiskConfig,
    DeliverySimulationResult,
    DeliveryStressResult,
    Feature,
    OptimizationResult,
    PnLAssessment,
    PortfolioPnLLayers,
    PortfolioProfitabilityResult,
    RiskManagementROI,
    ScenarioRiskModel,
)
from fhs.core.services import RiskCalculator
from fhs.core.services.risk import (
    DeliveryRiskService,
    PortfolioLayerRiskService,
    SprintOverrunService,
)


@dataclass(frozen=True)
class ProfitOptimizationComparison:
    """Notebook-ready comparison of profit-tail optimization strategies."""

    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


def _cvar_budget_pressure(cvar: float, total_planned: float) -> float:
    """Normalised CVaR budget pressure: CVaR / total_planned_cost - 1."""
    if total_planned <= 0:
        return float("inf")  # pragma: no cover - defensive
    return cvar / total_planned - 1.0


class DeliveryAnalysisOperations:
    """Development risk, sprint overruns, and profitability analysis with explicit context."""

    def __init__(self, context: PortfolioContext):
        self._context = context
        self._risk_calculator = RiskCalculator()
        self._feature_by_name = {feature.name: feature for feature in context.features}

    @staticmethod
    def _display_name(name: str) -> str:
        return name.split(": ", 1)[-1]

    @staticmethod
    def _profit_tail_metrics(
        profit_scenarios: np.ndarray,
        *,
        alpha: float,
    ) -> tuple[float, float]:
        var_level = (1.0 - alpha) * 100.0
        tail_floor = float(np.percentile(profit_scenarios, var_level))
        tail_losses = profit_scenarios[profit_scenarios <= tail_floor]
        tail_mean = float(np.mean(tail_losses)) if len(tail_losses) > 0 else tail_floor
        return tail_floor, tail_mean

    @staticmethod
    def _delivery_business_value_scenarios(
        base_scenarios: np.ndarray,
        *,
        target_scenarios: int,
        seed: int,
    ) -> np.ndarray:
        """Return development-specific business-value scenarios with configured length."""
        source = np.asarray(base_scenarios, dtype=float)
        if len(source) == target_scenarios:
            return np.array(source, copy=True)

        rng = np.random.default_rng(seed)
        indices = rng.choice(
            len(source),
            size=target_scenarios,
            replace=target_scenarios > len(source),
        )
        return source[indices]

    @staticmethod
    def _portfolio_cost_tail_metrics(
        portfolio_costs: np.ndarray,
        *,
        alpha: float,
    ) -> tuple[float, float]:
        """Return portfolio Cost-at-Risk and CVaR for the configured alpha."""
        car = float(np.percentile(portfolio_costs, alpha * 100))
        tail = portfolio_costs[portfolio_costs >= car]
        cvar = float(np.mean(tail)) if len(tail) > 0 else car
        return car, cvar

    # noinspection PyTypeHintsInspection
    def stress_test(
        self,
        feature_names: Iterable[str],
        *,
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        fail_multiplier: float = 1.0,
        delay_multiplier: float = 1.0,
        shock_sensitivity: float = 1.0,
        seed: int = 42,
    ) -> DeliveryStressResult:
        """Simulate development execution stress with delay and failure effects."""
        normalized_risk_model = PortfolioLayerRiskService.normalize_risk_model(
            risk_model
        )
        return DeliveryRiskService.stress_test_delivery(
            selected=self._context.resolve_names(feature_names),
            feature_by_name=self._feature_by_name,
            simulation_results=self._context.simulation_results,
            risk_model=normalized_risk_model,
            scenarios=self._context.scenarios,
            fail_multiplier=fail_multiplier,
            delay_multiplier=delay_multiplier,
            shock_sensitivity=shock_sensitivity,
            seed=seed,
        )

    def simulate_risk(
        self,
        feature_names: Iterable[str],
        *,
        delivery_config: DeliveryRiskConfig,
        seed: int = 42,
    ) -> dict[str, DeliverySimulationResult]:
        """Simulate sprint overrun and cost risk for selected features."""
        selected = self._context.resolve_names(feature_names)
        if not selected:
            return {}  # pragma: no cover - defensive

        selected_features = [self._feature_by_name[name] for name in selected]
        sprint_plans = SprintOverrunService.compute_sprint_plans(
            selected_features,
            config=delivery_config,
        )
        if not sprint_plans:
            return {}  # pragma: no cover - defensive

        results: dict[str, DeliverySimulationResult] = {}
        target_scenarios = int(delivery_config.scenarios)
        for index, feature in enumerate(selected_features):
            if feature.name not in sprint_plans:
                continue  # pragma: no cover - defensive

            base_simulation = self._context.simulation_results.get(feature.name)
            if base_simulation is None:
                continue  # pragma: no cover - defensive

            adjusted_business_value = self._delivery_business_value_scenarios(
                np.asarray(base_simulation.results_array),
                target_scenarios=target_scenarios,
                seed=seed + index,
            )

            results[feature.name] = SprintOverrunService.simulate_delivery(
                feature=feature,
                sprint_plan=sprint_plans[feature.name],
                business_value_after_risk=adjusted_business_value,
                config=delivery_config,
                seed=seed + index,
            )

        return results

    def profitability(
        self,
        feature_names: Iterable[str],
        delivery_results: dict[str, DeliverySimulationResult],
    ) -> PortfolioProfitabilityResult:
        """Combine business-value-after-risk and simulated delivery cost into profit layers."""
        selected = self._context.resolve_names(feature_names)
        selected_set = set(selected)
        selected_features = [self._feature_by_name[name] for name in selected]
        filtered_results = {
            name: result
            for name, result in delivery_results.items()
            if name in selected_set
        }
        return SprintOverrunService.compute_profitability(
            delivery_results=filtered_results,
            features=selected_features,
        )

    @staticmethod
    def profitability_rows(
        profitability: PortfolioProfitabilityResult,
    ) -> list[tuple[str, ...]]:
        """Notebook-ready profitability table with values only."""
        return [
            (
                result.feature_name.split(": ", 1)[-1],
                f"{result.break_even_probability:.1%}",
                f"EUR {result.expected_profit:,.0f}",
                f"EUR {result.expected_loss:,.0f}",
                f"EUR {result.loss_at_risk_95:,.0f}",
                f"{result.profit_margin:.1%}",
            )
            for result in profitability.feature_results
        ]

    @staticmethod
    def sprint_plan_rows(
        features: Iterable[Any],
        _delivery_config: DeliveryRiskConfig,
    ) -> list[tuple[str, ...]]:
        """Notebook-ready sprint-plan rows per feature."""
        rows: list[tuple[str, ...]] = []
        for feature in features:
            planned_weeks = float(feature.development_weeks or 0.0)
            planned_sprints = SprintOverrunService.planned_sprints_for_weeks(
                planned_weeks,
                sprint_length_weeks=float(_delivery_config.sprint_length_weeks),
            )
            rows.append(
                (
                    feature.name.split(": ", 1)[-1],
                    f"{planned_weeks:.1f}",
                    str(planned_sprints),
                    f"EUR {feature.development_cost:,.0f}",
                )
            )
        return rows

    @staticmethod
    def delay_summary_rows(
        delivery_results: dict[str, DeliverySimulationResult],
        feature_names: Iterable[str] | None = None,
    ) -> list[tuple[str, ...]]:
        """Notebook-ready sprint-overrun summary rows."""
        ordered_names = (
            [name for name in feature_names if name in delivery_results]
            if feature_names is not None
            else sorted(delivery_results)
        )
        return [
            (
                name.split(": ", 1)[-1],
                str(delivery_results[name].planned_sprints),
                str(delivery_results[name].sprints_p50),
                str(delivery_results[name].sprints_p75),
                str(delivery_results[name].sprints_p95),
                f"+{delivery_results[name].sprints_p50 - delivery_results[name].planned_sprints}",
                f"+{delivery_results[name].sprints_p75 - delivery_results[name].planned_sprints}",
                f"+{delivery_results[name].sprints_p95 - delivery_results[name].planned_sprints}",
                f"{delivery_results[name].cancelled_pct:.1%}",
            )
            for name in ordered_names
        ]

    @staticmethod
    def cost_comparison_rows(
        features: Iterable[Feature],
        delivery_results: dict[str, DeliverySimulationResult],
    ) -> list[tuple[str, ...]]:
        """Notebook-ready feature-investment vs development-burn rows per feature."""
        rows: list[tuple[str, ...]] = []
        for feature in features:
            result = delivery_results.get(feature.name)
            if result is None:
                continue
            planned_investment = float(feature.development_cost)
            cost_uplift = float(getattr(result, "cost_uplift", 0.0))
            planned_delivery = (
                float(result.expected_actual_cost) / (1.0 + cost_uplift)
                if (1.0 + cost_uplift) > 0
                else 0.0
            )
            expected = float(result.expected_actual_cost)
            p95 = float(result.cost_p95)
            uplift = (
                (expected / planned_delivery - 1.0) if planned_delivery > 0 else 0.0
            )
            rows.append(
                (
                    feature.name.split(": ", 1)[-1],
                    f"EUR {planned_investment:,.0f}",
                    f"EUR {planned_delivery:,.0f}",
                    f"EUR {expected:,.0f}",
                    f"EUR {p95:,.0f}",
                    f"{uplift:+.1%}",
                )
            )
        return rows

    @staticmethod
    def budget_fit_rows(
        features: Iterable[Feature],
        delivery_results: dict[str, DeliverySimulationResult],
    ) -> list[tuple[str, ...]]:
        """Notebook-ready budget-fit ranking rows sorted by budget pressure.

        Budget pressure uses **CVaR 95%** (mean of the worst 5% of cost
        scenarios) rather than the discrete CaR 95% percentile, because
        sprint-based costs are step functions and the raw percentile often
        falls on identical multiples for every feature.

        Columns: Priority | Feature | Planned investment |
                 CVaR 95% (worst-5% avg) | Budget pressure
        """
        raw: list[dict[str, Any]] = []
        for feature in features:
            result = delivery_results.get(feature.name)
            if result is None:
                continue
            planned = float(feature.development_cost)
            cvar = float(result.cost_cvar)
            pressure = (cvar / planned - 1.0) if planned > 0 else 0.0
            raw.append(
                {
                    "name": feature.name,
                    "planned": planned,
                    "cvar": cvar,
                    "pressure": pressure,
                }
            )
        raw.sort(key=lambda r: r["pressure"])
        return [
            (
                str(idx),
                r["name"].split(": ", 1)[-1],
                f"EUR {r['planned']:,.0f}",
                f"EUR {r['cvar']:,.0f}",
                f"{r['pressure']:+.1%}",
            )
            for idx, r in enumerate(raw, 1)
        ]

    @staticmethod
    def budget_fit_summary(
        features: Iterable[Feature],
        delivery_results: dict[str, DeliverySimulationResult],
        budget: float,
    ) -> dict[str, float]:
        """Compute portfolio-level budget summary using CVaR 95%.

        Returns dict with keys:
        ``budget``, ``planned_total``, ``cvar_total``, ``budget_gap``.
        """
        planned_total = 0.0
        cvar_total = 0.0
        for feature in features:
            result = delivery_results.get(feature.name)
            if result is None:
                continue
            planned_total += float(feature.development_cost)
            cvar_total += float(result.cost_cvar)
        return {
            "budget": budget,
            "planned_total": planned_total,
            "cvar_total": cvar_total,
            "budget_gap": cvar_total - budget,
        }

    @staticmethod
    def delivery_cost_risk_rows(
        features: Iterable[Feature],
        delivery_results: dict[str, DeliverySimulationResult],
    ) -> list[tuple[str, ...]]:
        """Notebook-ready VaR/CVaR development cost table rows per feature.

        Columns: Feature | Planned investment | Expected cost |
                 Cost at Risk 95% (CaR) | CVaR (worst-5% avg) |
                 Uplift vs plan | Cancelled %
        """
        rows: list[tuple[str, ...]] = []
        for feature in features:
            result = delivery_results.get(feature.name)
            if result is None:
                continue
            planned = float(feature.development_cost)
            expected = float(result.expected_actual_cost)
            car95 = float(result.cost_p95)
            cvar = float(result.cost_cvar)
            uplift = (expected / planned - 1.0) if planned > 0 else 0.0
            cancelled = float(result.cancelled_pct)
            rows.append(
                (
                    feature.name.split(": ", 1)[-1],
                    f"EUR {planned:,.0f}",
                    f"EUR {expected:,.0f}",
                    f"EUR {car95:,.0f}",
                    f"EUR {cvar:,.0f}",
                    f"{uplift:+.1%}",
                    f"{cancelled:.1%}",
                )
            )
        return rows

    @staticmethod
    def min_cost_cvar_selection(
        features: Iterable[Feature],
        delivery_results: dict[str, DeliverySimulationResult],
        budget: float,
        alpha: float = 0.95,
    ) -> dict[str, Any]:
        """Select the largest feasible feature subset with the lowest portfolio CVaR.

        Primary objective: maximise the number of features selected (as many as
        possible within the scenario budget).
        Secondary objective: among all combinations of that maximum count that fit
        within the budget, pick the one with the lowest **normalised** portfolio
        CVaR 95% — i.e. the lowest portfolio budget pressure:
        pressure = CVaR_95% / total_planned_cost - 1.

        Normalisation is necessary because combinations with different total planned
        costs are not comparable on an absolute CVaR scale: a cheaper combination
        always has a lower absolute CVaR regardless of risk efficiency.  Dividing by
        total_planned_cost removes the cost-scale effect and asks "by how much does
        the worst-case expected cost exceed the total planned investment, proportionally?"
        — fair across features with different durations and budgets.

        CVaR is preferred over CaR as the tail metric because it is a coherent risk
        measure: it captures the expected development cost across the entire worst
        (1-alpha) tail, not just the boundary percentile.

        Returns a dict with keys:
        ``selected`` (list[str]), ``total_planned_cost``, ``budget_remaining``,
        ``budget_pressure``, ``expected_cost``, ``portfolio_car``, ``portfolio_cvar``.
        """
        from itertools import combinations

        feature_list = [f for f in features if f.name in delivery_results]

        # Step 1: find the maximum number of features that fit within budget.
        max_count = 0
        for r in range(len(feature_list), 0, -1):
            for combo in combinations(feature_list, r):
                if sum(float(f.development_cost) for f in combo) <= budget:
                    max_count = r
                    break
            if max_count > 0:
                break

        if max_count == 0:
            return {}

        # Step 2: among all max_count-feature combos within budget, minimise normalised
        # CVaR 95% (= portfolio budget pressure: CVaR / total_planned_cost - 1).
        # Normalisation is required because combinations with different total costs
        # are not comparable on an absolute CVaR scale — a cheaper combination always
        # has lower absolute CVaR regardless of risk efficiency.  The ratio removes
        # the cost-scale effect and asks: "by how much does the worst-case expected
        # cost exceed the total planned investment, proportionally?"
        best: dict[str, Any] = {}
        best_pressure = float("inf")

        for combo in combinations(feature_list, max_count):
            total_planned = sum(float(f.development_cost) for f in combo)
            if total_planned > budget:
                continue
            portfolio_costs: np.ndarray = sum(  # type: ignore[assignment]
                delivery_results[f.name].actual_cost for f in combo
            )
            car, cvar = DeliveryAnalysisOperations._portfolio_cost_tail_metrics(
                portfolio_costs,
                alpha=alpha,
            )
            pressure = _cvar_budget_pressure(cvar, total_planned)
            if pressure < best_pressure:
                best_pressure = pressure
                best = {
                    "selected": [f.name for f in combo],
                    "total_planned_cost": total_planned,
                    "budget_remaining": budget - total_planned,
                    "budget_pressure": pressure,
                    "expected_cost": float(np.mean(portfolio_costs)),
                    "portfolio_car": car,
                    "portfolio_cvar": cvar,
                }

        return best

    @staticmethod
    def cost_risk_combination_rows(
        features: Iterable[Feature],
        delivery_results: dict[str, DeliverySimulationResult],
        budget: float,
        alpha: float = 0.95,
    ) -> list[tuple[str, ...]]:
        """Notebook-ready comparison rows for all budget-feasible combinations.

        Sort order mirrors the selection objective:
        1) maximise feature count, 2) minimise normalised CVaR pressure,
        3) minimise absolute portfolio CVaR.
        """
        from itertools import combinations

        feature_list = [f for f in features if f.name in delivery_results]
        if not feature_list:
            return []

        selection = DeliveryAnalysisOperations.min_cost_cvar_selection(
            feature_list,
            delivery_results,
            budget,
            alpha=alpha,
        )
        selected_names = frozenset(selection.get("selected", []))

        raw: list[dict[str, Any]] = []
        for r in range(1, len(feature_list) + 1):
            for combo in combinations(feature_list, r):
                total_planned = sum(float(f.development_cost) for f in combo)
                if total_planned > budget:
                    continue
                portfolio_costs: np.ndarray = sum(  # type: ignore[assignment]
                    delivery_results[f.name].actual_cost for f in combo
                )
                car, cvar = DeliveryAnalysisOperations._portfolio_cost_tail_metrics(
                    portfolio_costs,
                    alpha=alpha,
                )
                pressure = (
                    cvar / total_planned - 1.0 if total_planned > 0 else float("inf")
                )
                combo_names = [f.name for f in combo]
                raw.append(
                    {
                        "names": combo_names,
                        "count": len(combo_names),
                        "planned": total_planned,
                        "remaining": budget - total_planned,
                        "car": car,
                        "cvar": cvar,
                        "pressure": pressure,
                        "is_selected": frozenset(combo_names) == selected_names,
                    }
                )

        raw.sort(
            key=lambda item: (
                -int(item["count"]),
                float(item["pressure"]),
                float(item["cvar"]),
                float(item["planned"]),
            )
        )

        return [
            (
                str(idx),
                "Yes" if bool(row["is_selected"]) else "",
                str(int(row["count"])),
                ", ".join(
                    DeliveryAnalysisOperations._display_name(name)
                    for name in row["names"]
                ),
                f"EUR {float(row['planned']):,.0f}",
                f"EUR {float(row['remaining']):,.0f}",
                f"EUR {float(row['cvar']):,.0f}",
                f"{float(row['pressure']):+.1%}",
            )
            for idx, row in enumerate(raw, 1)
        ]

    def optimize_profit_cvar(
        self,
        feature_names: Iterable[str],
        delivery_results: dict[str, DeliverySimulationResult],
        *,
        budget: float | None = None,
        alpha: float = 0.95,
        n_scenarios: int = 300,
    ) -> OptimizationResult:
        """Optimize portfolio by minimizing CVaR on profit scenarios.

        Profit scenarios are built per feature as:
        business value after all risks minus simulated development cost.
        The CVaR MILP solver (Rockafellar-Uryasev) finds the feature subset
        that minimises tail-risk of the portfolio profit distribution.
        """
        from fhs.core.services import PortfolioViewService
        from fhs.core.services.optimization.solvers.cvar_milp_solver import (
            CVaRMILPSolver,
        )

        selected = self._context.resolve_names(feature_names)
        if not selected:
            raise ValueError(
                "feature_names must not be empty"
            )  # pragma: no cover - defensive

        missing = [name for name in selected if name not in delivery_results]
        if missing:
            raise ValueError(
                f"Missing delivery simulation results for features: {sorted(missing)}"
            )

        profit_scenarios = {name: delivery_results[name].profit for name in selected}
        costs = {
            name: self._feature_by_name[name].development_cost for name in selected
        }

        solver = CVaRMILPSolver(
            risk_calculator=self._risk_calculator,
            n_scenarios=n_scenarios,
            seed=self._context.seed,
        )
        solver_result = solver.solve_from_profit_scenarios(
            profit_scenarios=profit_scenarios,
            costs=costs,
            budget=float(self._context.budget if budget is None else budget),
            alpha=alpha,
        )

        return PortfolioViewService.optimization_result_from_solver_result(
            solver_result
        )

    @staticmethod
    def _validate_profit_feature_names(
        selected_names: list[str],
        delivery_results: dict[str, DeliverySimulationResult],
    ) -> None:
        if not selected_names:
            raise ValueError(
                "feature_names must not be empty"
            )  # pragma: no cover - defensive
        missing_names = [
            name for name in selected_names if name not in delivery_results
        ]
        if missing_names:
            raise ValueError(  # pragma: no cover - defensive
                f"Missing delivery simulation results for features: {sorted(missing_names)}"
            )

    @staticmethod
    def _greedy_selection_by_profit_ratio(
        selected_names: list[str],
        comparison_budget: float,
        feature_by_name: dict[str, Feature],
        delivery_results: dict[str, DeliverySimulationResult],
    ) -> tuple[list[str], float]:
        ratios = []
        for name in selected_names:
            planned_cost = feature_by_name[name].development_cost
            expected_profit = float(np.mean(delivery_results[name].profit))
            ratio = expected_profit / planned_cost if planned_cost > 0 else -1e9
            ratios.append((ratio, name))
        ratios.sort(reverse=True)

        baseline_selected: list[str] = []
        remaining = comparison_budget
        for _, name in ratios:
            cost = feature_by_name[name].development_cost
            if cost <= remaining:  # pragma: no cover - partial branch
                baseline_selected.append(name)
                remaining -= cost
        return baseline_selected, remaining

    @staticmethod
    def _profit_tail_for_names(
        names: list[str],
        delivery_results: dict[str, DeliverySimulationResult],
        alpha: float,
    ) -> tuple[float, float]:
        if not names:
            return 0.0, 0.0  # pragma: no cover - defensive
        profit = np.sum([delivery_results[name].profit for name in names], axis=0)
        return DeliveryAnalysisOperations._profit_tail_metrics(profit, alpha=alpha)

    def profit_optimization_comparison(
        self,
        feature_names: Iterable[str],
        delivery_results: dict[str, DeliverySimulationResult],
        *,
        budget: float | None = None,
        alpha: float = 0.95,
        n_scenarios: int | None = None,
    ) -> ProfitOptimizationComparison:
        """Compare CVaR optimization against a greedy expected-profit baseline."""
        selected = self._context.resolve_names(feature_names)
        self._validate_profit_feature_names(selected, delivery_results)

        comparison_budget = float(self._context.budget if budget is None else budget)
        scenario_count = (
            n_scenarios
            if n_scenarios is not None
            else len(next(iter(delivery_results.values())).profit)
        )
        profit_cvar = self.optimize_profit_cvar(
            selected,
            delivery_results,
            budget=comparison_budget,
            alpha=alpha,
            n_scenarios=scenario_count,
        )
        baseline_selected, remaining_budget = self._greedy_selection_by_profit_ratio(
            selected,
            comparison_budget,
            self._feature_by_name,
            delivery_results,
        )
        baseline_tail_floor, baseline_tail_mean = self._profit_tail_for_names(
            baseline_selected, delivery_results, alpha
        )
        optimized_tail_floor, optimized_tail_mean = self._profit_tail_for_names(
            profit_cvar.recommended_features, delivery_results, alpha
        )

        var_level = round((1.0 - alpha) * 100.0)
        cvar_label = round(alpha * 100.0)

        headers = (
            "Method",
            "Selected features",
            "Total cost",
            f"Tail floor (P{var_level})",
            f"Tail mean (CVaR {cvar_label}%)",
        )
        rows = (
            (
                f"Profit-CVaR MILP (alpha={alpha:.0%})",
                ", ".join(
                    self._display_name(name)
                    for name in profit_cvar.recommended_features
                )
                or "None",
                f"EUR {profit_cvar.total_cost:,.0f}",
                f"EUR {optimized_tail_floor:,.0f}",
                f"EUR {optimized_tail_mean:,.0f}",
            ),
            (
                "Expected-profit ratio baseline",
                ", ".join(self._display_name(name) for name in baseline_selected)
                or "None",
                f"EUR {comparison_budget - remaining_budget:,.0f}",
                f"EUR {baseline_tail_floor:,.0f}",
                f"EUR {baseline_tail_mean:,.0f}",
            ),
        )
        return ProfitOptimizationComparison(headers=headers, rows=rows)

    @staticmethod
    def risk_management_assessment(
        scenarios: dict[str, DeliveryStressResult],
        *,
        investment: float,
        baseline_label: str = "Baseline",
        managed_label: str = "Managed",
        program_cost_share: float = 0.06,
    ) -> RiskManagementROI:
        """Compare baseline and managed delivery stress to derive ROI metrics."""
        return DeliveryRiskService.risk_management_assessment(
            scenarios,
            investment=investment,
            baseline_label=baseline_label,
            managed_label=managed_label,
            program_cost_share=program_cost_share,
        )

    @staticmethod
    def pnl_assessment(
        pnl_layers: PortfolioPnLLayers,
        *,
        investment: float,
    ) -> PnLAssessment:
        """Assess expected and downside break-even against investment."""
        return DeliveryRiskService.pnl_assessment(
            pnl_layers,
            investment=investment,
        )
