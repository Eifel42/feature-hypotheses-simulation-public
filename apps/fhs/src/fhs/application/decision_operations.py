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

"""Decision/reporting operations with explicit portfolio context."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Any, cast

import numpy as np

from fhs.application.portfolio_context import PortfolioContext
from fhs.core.model import (
    BudgetFrontierRow,
    BudgetRiskRow,
    ConcentrationResult,
    Feature,
    FeatureRanking,
    NegativeScoreReport,
    OptimizationResult,
    PortfolioSnapshot,
    StrategyCategoryCostRow,
)
from fhs.core.services import (
    PortfolioDecisionSupportService,
    PortfolioViewService,
    build_correlation_matrix_from_clusters,
)


class DecisionOperations:
    """Composed decision/reporting operations with explicit context dependency."""

    def __init__(self, context: PortfolioContext):
        self._context = context

    @staticmethod
    def compare_solvers(
        include: Sequence[str] = ("exact", "ilp", "greedy"),
        *,
        budget: float | None = None,
        strategy: str = "var_floor",
        optimize_fn: Callable[..., Any],
    ) -> dict[str, OptimizationResult]:
        """Compare multiple solvers using provided optimization function.

        Args:
            include: Solver names to include in comparison.
            budget: Budget constraint, defaults to context budget.
            strategy: Optimization strategy.
            optimize_fn: Function to call for optimization (from host).

        Returns:
            Dictionary mapping solver names to optimization results.
        """
        return {
            solver: optimize_fn(
                solver=solver,
                budget=budget,
                strategy=strategy,
            )
            for solver in include
        }

    def rank_features(self, strategy: str = "var_floor") -> list[FeatureRanking]:
        return PortfolioDecisionSupportService.rank_features(
            features=self._context.features,
            simulation_results=self._context.simulation_results,
            strategy=strategy,
        )

    def negative_score_analysis(
        self,
        *,
        budget: float | None = None,
        strategy: str = "var_floor",
        spawn_subset_fn: Callable[..., Any],
        optimize_fn: Callable[..., Any],
    ) -> NegativeScoreReport:
        """Analyze features with negative scores.

        Args:
            budget: Budget constraint, defaults to context budget.
            strategy: Optimization strategy.
            spawn_subset_fn: Function to create subset service (from host).
            optimize_fn: Function to run optimization on the subset service.

        Returns:
            Negative score analysis report.
        """
        budget_value = float(self._context.budget if budget is None else budget)

        def solve_candidates(
            candidate_names: tuple[str, ...] | None,
        ) -> dict[str, OptimizationResult]:
            if candidate_names is None:
                # Use full feature set for baseline comparison
                return self.compare_solvers(
                    budget=budget_value,
                    strategy=strategy,
                    include=("exact", "ilp"),
                    optimize_fn=lambda **kwargs: optimize_fn(**kwargs),
                )

            candidate_set = set(candidate_names)
            subset_features = [
                feature
                for feature in self._context.features
                if feature.name in candidate_set
            ]
            subset_service = spawn_subset_fn(subset_features, budget=budget_value)
            return cast(
                dict[str, OptimizationResult],
                subset_service.compare_solvers(
                    budget=budget_value,
                    strategy=strategy,
                    include=("exact", "ilp"),
                ),
            )

        return PortfolioDecisionSupportService.negative_score_analysis(
            features=self._context.features,
            simulation_results=self._context.simulation_results,
            solve_candidates=solve_candidates,
        )

    def strategy_category_cost_share(
        self,
        selected_names: Iterable[str],
        strategy: dict[str, Any],
    ) -> tuple[StrategyCategoryCostRow, ...]:
        feature_by_name = {f.name: f for f in self._context.features}
        return PortfolioDecisionSupportService.strategy_category_cost_share(
            selected_names=selected_names,
            feature_by_name=feature_by_name,
            strategy=strategy,
        )

    @staticmethod
    def budget_risk_path(
        levels: dict[str, float],
        *,
        solver: str = "ilp",
        strategy: str = "var_floor",
        seed: int = 42,
        systematic_shock_probability: float = 0.05,
        systematic_shock_multiplier: float = 0.30,
        optimize_fn: Callable[..., Any],
        analyze_delivery_risk_fn: Callable[..., Any],
    ) -> list[BudgetRiskRow]:
        """Compute budget risk path across multiple budget levels.

        Args:
            levels: Budget levels to analyze.
            solver: Solver to use.
            strategy: Optimization strategy.
            seed: Random seed.
            systematic_shock_probability: Probability of systematic shock.
            systematic_shock_multiplier: Multiplier for systematic shock.
            optimize_fn: Function to call for optimization (from host).
            analyze_delivery_risk_fn: Function to analyze delivery risk (from optimizer).

        Returns:
            List of budget risk rows.
        """
        return PortfolioDecisionSupportService.budget_risk_path(
            levels=levels,
            optimize_for_budget=lambda budget: optimize_fn(
                solver=solver,
                budget=budget,
                strategy=strategy,
            ),
            analyze_delivery_risk=analyze_delivery_risk_fn,
            seed=seed,
            systematic_shock_probability=systematic_shock_probability,
            systematic_shock_multiplier=systematic_shock_multiplier,
        )

    def feature_score_analysis(self) -> dict[str, float]:
        return PortfolioDecisionSupportService.feature_score_analysis(
            features=self._context.features,
            simulation_results=self._context.simulation_results,
        )

    def budget_sensitivity(
        self,
        levels: dict[str, float],
        *,
        solver: str = "ilp",
        strategy: str = "var_floor",
        optimize_fn: Callable[..., Any],
    ) -> dict[str, OptimizationResult]:
        """Compute budget sensitivity across multiple budget levels.

        Args:
            levels: Budget levels to analyze.
            solver: Solver to use.
            strategy: Optimization strategy.
            optimize_fn: Function to call for optimization (from host).

        Returns:
            Dictionary mapping budget level names to optimization results.
        """
        return PortfolioDecisionSupportService.budget_sensitivity(
            levels=levels,
            features=self._context.features,
            simulation_results=self._context.simulation_results,
            optimize_for_budget=lambda budget: optimize_fn(
                solver=solver,
                budget=budget,
                strategy=strategy,
            ),
        )

    @staticmethod
    def budget_frontier(
        budgets: list[float],
        *,
        solver: str = "ilp",
        strategy: str = "var_floor",
        optimize_fn: Callable[..., Any],
    ) -> list[BudgetFrontierRow]:
        """Compute efficient frontier across budget levels.

        Args:
            budgets: Budget levels to analyze.
            solver: Solver to use.
            strategy: Optimization strategy.
            optimize_fn: Function to call for optimization (from host).

        Returns:
            List of budget frontier rows.
        """
        return PortfolioViewService.budget_frontier_rows(
            budgets=budgets,
            optimize_for_budget=lambda budget: optimize_fn(
                solver=solver,
                budget=budget,
                strategy=strategy,
            ),
        )

    def concentration(self, names: Iterable[str] | None = None) -> ConcentrationResult:
        subset = self._context.subset_results(names)
        expected = {
            name: float(result.expected_business_value)
            for name, result in subset.items()
        }
        return PortfolioViewService.concentration_from_expected_business_values(
            expected
        )

    def stress_scenarios(
        self,
        names: Iterable[str] | None = None,
        portfolio_snapshot_fn: Callable[..., Any] | None = None,
    ) -> dict[str, Any]:
        """Compute stress scenario analysis.

        Args:
            names: Feature names to include, or None for all.
            portfolio_snapshot_fn: Function to compute portfolio snapshot (from host).

        Returns:
            Dictionary with stress scenario metrics.
        """
        resolved = self._context.resolve_names(names)
        subset = self._context.subset_results(resolved)
        feature_by_name = {f.name: f for f in self._context.features}

        components = {
            name: result.results_array
            * feature_by_name[name].business_value_per_conversion
            for name, result in subset.items()
        }
        baseline = portfolio_snapshot_fn(resolved) if portfolio_snapshot_fn else None
        if baseline is None:
            baseline_array = (
                np.sum(list(components.values()), axis=0)
                if components
                else np.array([], dtype=float)
            )
            investment = float(
                sum(
                    feature_by_name[name].development_cost
                    for name in resolved
                    if name in feature_by_name
                )
            )
            baseline = PortfolioSnapshot(
                expected=float(np.mean(baseline_array)) if len(baseline_array) else 0.0,
                var_95=(
                    float(np.percentile(baseline_array, 5))
                    if len(baseline_array)
                    else 0.0
                ),
                cvar_95=(
                    float(
                        np.mean(
                            baseline_array[
                                baseline_array
                                <= float(np.percentile(baseline_array, 5))
                            ]
                        )
                    )
                    if len(baseline_array)
                    else 0.0
                ),
                std_dev=float(np.std(baseline_array)) if len(baseline_array) else 0.0,
                investment=investment,
            )
        top_feature = (
            max(
                resolved,
                key=lambda name: (
                    self._context.simulation_results[name].expected_business_value
                ),
            )
            if resolved
            else None
        )
        return PortfolioViewService.stress_scenarios_view(
            resolved=resolved,
            baseline=baseline,
            components=components,
            top_feature=top_feature,
            is_high_delivery_risk=lambda name: (
                feature_by_name[name].likelihood_of_non_delivery > 0.25
            ),
        )

    def dependency_correlation(
        self,
        names: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        resolved = self._context.resolve_names(names)
        feature_by_name = {f.name: f for f in self._context.features}
        selected = [feature_by_name[name] for name in resolved]
        labels = [feature.name for feature in selected]
        dependency_matrix = build_correlation_matrix_from_clusters(selected)
        business_value_arrays = (
            np.column_stack(
                [
                    self._context.simulation_results[name].results_array
                    * feature_by_name[name].business_value_per_conversion
                    for name in resolved
                ]
            )
            if resolved
            else np.array([[]], dtype=float)
        )
        return PortfolioViewService.dependency_correlation_view(
            labels=labels,
            dependency_matrix=dependency_matrix,
            business_value_arrays=business_value_arrays,
        )

    def risk_contribution_rows(
        self,
        names: Iterable[str] | None = None,
    ) -> list[tuple[str, float, float, float, float, float]]:
        resolved = self._context.resolve_names(names)  # pragma: no cover - defensive
        portfolio = (
            self._context.sum_portfolio_scenarios(  # pragma: no cover - defensive
                self._context.subset_results(resolved)  # pragma: no cover - defensive
            )
        )  # pragma: no cover - defensive
        feature_by_name = {
            f.name: f for f in self._context.features
        }  # pragma: no cover - defensive
        return PortfolioDecisionSupportService.risk_contribution_rows(  # pragma: no cover - defensive
            names=resolved,
            feature_by_name=feature_by_name,
            simulation_results=self._context.simulation_results,
            portfolio_scenarios=portfolio,
        )

    def feature_overview_rows(self) -> list[tuple[str, ...]]:
        """Rows for feature-level overview table."""
        return PortfolioDecisionSupportService.feature_overview_rows(
            features=self._context.features,
            simulation_results=self._context.simulation_results,
        )

    # noinspection PyTypeHintsInspection
    def llp_rows(self) -> list[tuple[str, ...]]:
        """Rows with LLP and delivery-adjusted risk exposure."""
        return PortfolioDecisionSupportService.llp_rows(
            features=self._context.features,
            simulation_results=self._context.simulation_results,
        )

    @staticmethod
    # noinspection PyTypeHintsInspection
    def _result_field(result: OptimizationResult | dict[str, Any], key: str) -> Any:
        """Read solver-result fields from model objects or dict snapshots."""
        if isinstance(result, dict):
            return result.get(key)  # pragma: no cover - defensive
        return getattr(result, key, None)

    # noinspection PyTypeHintsInspection
    def solver_comparison_rows(
        self,
        solver_results: dict[str, OptimizationResult | dict[str, Any]],
        *,
        include: Sequence[str] = ("exact", "ilp", "greedy"),
    ) -> list[tuple[str, ...]]:
        """Notebook-ready solver comparison rows."""
        method_names = {
            "exact": "Exact",
            "ilp": "Linear (ILP)",
            "greedy": "Greedy",
        }
        rows: list[tuple[str, ...]] = []
        for key in include:
            result = solver_results.get(key)
            if result is None:
                continue
            recommended = self._result_field(result, "recommended_features") or ()
            rows.append(
                (
                    method_names.get(key, key.title()),
                    str(len(recommended)),
                    f"EUR {float(self._result_field(result, 'total_cost') or 0.0):,.0f}",
                    f"EUR {float(self._result_field(result, 'portfolio_expected') or 0.0):,.0f}",
                    f"EUR {float(self._result_field(result, 'portfolio_var_95') or 0.0):,.0f}",
                    f"{float(self._result_field(result, 'portfolio_roi') or 0.0):.0%}",
                    f"EUR {float(self._result_field(result, 'safety_buffer') or 0.0):,.0f}",
                    f"{float(self._result_field(result, 'computation_time_sec') or 0.0):.4f}s",
                )
            )
        return rows

    # noinspection PyTypeHintsInspection
    def negative_score_rows(
        self,
        *,
        features: Sequence[Feature] | None = None,
        simulation_results: dict[str, Any] | None = None,
    ) -> NegativeScoreRowsView:
        """Notebook-ready rows for per-feature var_floor score inspection."""
        ordered_features = (
            list(features) if features is not None else self._context.features
        )
        sim_results = (
            simulation_results
            if simulation_results is not None
            else self._context.simulation_results
        )

        rows_with_score: list[tuple[float, tuple[str, ...]]] = []
        positive_features: list[str] = []
        negative_features: list[str] = []

        for feature in ordered_features:
            result = sim_results[feature.name]
            score = float(result.business_value_at_risk_95) - float(
                feature.development_cost
            )
            has_positive_score = score >= 0
            if has_positive_score:
                positive_features.append(feature.name)
            else:
                negative_features.append(feature.name)  # pragma: no cover - defensive
            rows_with_score.append(
                (
                    score,
                    (
                        feature.name,
                        f"EUR {feature.development_cost:,.0f}",
                        f"EUR {float(result.business_value_at_risk_95):,.0f}",
                        f"EUR {score:,.0f}",
                        (
                            "Positive — ILP considers"
                            if has_positive_score
                            else "Negative — ILP avoids"
                        ),
                    ),
                )
            )

        rows = [
            row for _score, row in sorted(rows_with_score, key=lambda item: item[0])
        ]
        return NegativeScoreRowsView(
            rows=rows,
            positive_features=positive_features,
            negative_features=negative_features,
        )

    # noinspection PyTypeHintsInspection
    def negative_score_comparison_rows(
        self,
        results_all: dict[str, OptimizationResult | dict[str, Any]],
        results_positive: dict[str, OptimizationResult | dict[str, Any]],
    ) -> list[tuple[str, ...]]:
        """Notebook-ready comparison rows for all vs positive-only candidate sets."""
        rows: list[tuple[str, ...]] = []
        for label, result_set in (
            ("All features", results_all),
            ("Positive-score only", results_positive),
        ):
            for method in ("exact", "ilp"):
                result = result_set.get(method)
                if result is None:
                    continue
                selected = self._result_field(result, "recommended_features") or ()
                selected_short = (
                    ", ".join(name.split(": ", 1)[-1] for name in selected) or "None"
                )
                rows.append(
                    (
                        label,
                        method.upper(),
                        selected_short,
                        str(len(selected)),
                        f"EUR {float(self._result_field(result, 'portfolio_var_95') or 0.0):,.0f}",
                        f"EUR {float(self._result_field(result, 'total_cost') or 0.0):,.0f}",
                    )
                )
        return rows

    @staticmethod
    def runtime_scaling_rows(
        runtime_data: dict[str, dict[str, list[float]]],
        budgets_by_feature_count: dict[int, float] | None = None,
        *,
        include: Sequence[str] = ("exact", "ilp", "greedy"),
    ) -> list[tuple[str, ...]]:
        """Notebook-ready runtime/floor rows from aggregated scaling data."""
        rows: list[tuple[str, ...]] = []
        for method in include:
            data = runtime_data.get(method, {})
            x_values = data.get("x", [])
            floor_values = data.get("floor", [])
            runtime_values = data.get("runtime", [])
            for n, floor, runtime in zip(
                x_values, floor_values, runtime_values, strict=False
            ):
                budget_value = (
                    None
                    if budgets_by_feature_count is None
                    else budgets_by_feature_count.get(int(n))
                )
                rows.append(
                    (
                        str(int(n)),
                        method.upper(),
                        (
                            f"EUR {float(budget_value):,.0f}"
                            if budget_value is not None
                            else "-"
                        ),
                        f"EUR {float(floor):,.0f}",
                        f"{float(runtime):.4f}s",
                    )
                )
        return rows

    def selected_portfolio_rows(
        self,
        selected_names: Iterable[str],
        strategy: dict[str, Any] | None = None,
    ) -> list[tuple[str, ...]]:
        """Notebook-ready detail rows for selected portfolio features."""
        strategy_map = strategy or {}
        feature_by_name = {feature.name: feature for feature in self._context.features}
        rows: list[tuple[str, ...]] = []
        for name in selected_names:
            feature = feature_by_name.get(name)
            result = self._context.simulation_results.get(name)
            if feature is None or result is None:
                continue
            meta = strategy_map.get(name, {})
            rows.append(
                (
                    name,
                    str(meta.get("category", "-")),
                    f"EUR {float(feature.development_cost):,.0f}",
                    f"EUR {float(result.expected_business_value):,.0f}",
                    f"EUR {float(result.business_value_at_risk_95):,.0f}",
                )
            )
        return rows

    def feature_selection_view(
        self,
        features: Sequence[Feature],
        ilp_results: dict[str, OptimizationResult],
        *,
        full_label: str = "100% Budget",
    ) -> FeatureSelectionView:
        """Build the feature-score table and analytics for the ILP selection cell.

        Replaces the 30-line for-loop with _eur_to_float() in notebook 04.
        Accesses numeric values directly from simulation_results and features
        instead of parsing pre-formatted strings.

        Returns a :class:`FeatureSelectionView` with:
        - ``rows`` / ``headers``: ready for ``show.sensitivity()``
        - ``selected_features``: names selected at *full_label*
        - ``all_proxy_score`` / ``selected_proxy_score``: var_floor totals
        - ``has_negative_roi``: True if any feature has negative expected ROI
        """
        sim = self._context.simulation_results
        feature_score = self.feature_score_analysis()

        full_result = ilp_results.get(full_label)
        selected_set = set(full_result.recommended_features) if full_result else set()

        rows: list[tuple[str, ...]] = []
        all_proxy_score = 0.0
        selected_proxy_score = 0.0
        has_negative_roi = False

        for feature in sorted(features, key=lambda f: f.name):
            result = sim[feature.name]
            expected_business_value = float(result.expected_business_value)
            var_95_business_value = float(result.business_value_at_risk_95)
            net_floor_score = feature_score[feature.name]
            feature_roi = (
                (expected_business_value - feature.development_cost)
                / feature.development_cost
                if feature.development_cost > 0
                else 0.0
            )

            if feature_roi < 0:
                has_negative_roi = True  # pragma: no cover - defensive

            all_proxy_score += net_floor_score
            is_selected = feature.name in selected_set
            if is_selected:  # pragma: no cover - partial branch
                selected_proxy_score += net_floor_score

            rows.append(
                (
                    feature.name,
                    f"EUR {feature.development_cost:,.0f}",
                    f"EUR {expected_business_value:,.0f}",
                    f"{feature_roi:.0%}",
                    f"EUR {var_95_business_value:,.0f}",
                    f"EUR {net_floor_score:,.0f}",
                    "Yes" if is_selected else "No",
                    "Build now" if is_selected else "Keep in backlog",
                    (
                        "Improves objective"
                        if net_floor_score >= 0
                        else "Would reduce objective"
                    ),
                )
            )

        return FeatureSelectionView(
            rows=rows,
            headers=(
                "Feature",
                "Cost",
                "Expected",
                "Feature ROI",
                "BVF 95%",
                "var_floor score (BVF 95% - Cost)",
                "Selected at 100%",
                "Backlog decision",
                "Impact on objective",
            ),
            selected_features=sorted(selected_set),
            all_proxy_score=all_proxy_score,
            selected_proxy_score=selected_proxy_score,
            has_negative_roi=has_negative_roi,
        )

    @staticmethod
    def decision_table_rows(
        budget_levels: dict[str, float],
        ilp_results: dict[str, OptimizationResult],
    ) -> list[tuple[str, ...]]:
        """Notebook-ready decision table rows for budget sensitivity results.

        Maps each budget level to a recommended action, selection note, and
        backlog guidance based on the ILP optimization outcome.

        Returns rows for use with show.sensitivity() and headers:
        ("Budget Level", "Budget", "ILP Selection", "Selection Note",
         "Backlog Guidance", "Expected", "Floor (BVF 95%)",
         "Safety Buffer", "Remaining Budget", "Suggested Action")
        """
        rows: list[tuple[str, ...]] = []
        for label, budget in budget_levels.items():
            result = ilp_results[label]
            selected = list(result.recommended_features)
            selected_text = (
                ", ".join(name.split(": ", 1)[-1] for name in selected) or "None"
            )

            if result.solver == "not_run":
                selection_note = result.message or "Not optimized"
                backlog_guidance = "Build none; keep all items in prioritized backlog"
                action = (
                    "Wait for budget or assumption change, then re-run optimization"
                )
            elif selected:
                selection_note = "Feasible portfolio selected"
                backlog_guidance = "Build selected now; keep others in backlog"
                action = "Track floor monthly and re-optimize next cycle"
            else:
                selection_note = "No build selected: review assumptions and objective"
                backlog_guidance = "Build none now; keep all items in backlog"
                action = "Recheck assumptions or objective before commitment"

            rows.append(
                (
                    label,
                    f"EUR {budget:,.0f}",
                    selected_text,
                    selection_note,
                    backlog_guidance,
                    f"EUR {result.portfolio_expected:,.0f}",
                    f"EUR {result.portfolio_var_95:,.0f}",
                    f"EUR {result.safety_buffer:,.0f}",
                    f"EUR {result.budget_remaining:,.0f}",
                    action,
                )
            )
        return rows

    @staticmethod
    def portfolio_comparison_rows(
        selection: FeatureSelectionView,
        selected_snapshot: PortfolioSnapshot,
        all_snapshot: PortfolioSnapshot,
        full_budget: float,
        all_feature_names: Sequence[str],
    ) -> PortfolioComparisonView:
        """Build portfolio comparison rows for ILP-selected vs. all-features option.

        Returns a :class:`PortfolioComparisonView` with formatted rows ready for
        ``show.sensitivity()``, comparing the ILP-selected portfolio against the
        full feature set. Useful when at least one feature has negative ROI.

        Args:
            selection: Result of ``feature_selection_view()``.
            selected_snapshot: Portfolio snapshot for ILP-selected features.
            all_snapshot: Portfolio snapshot for all features.
            full_budget: The 100% budget constraint.
            all_feature_names: Sorted list of all feature names.

        Returns:
            :class:`PortfolioComparisonView` with ``rows`` and ``headers``.
        """
        selected_label = (
            ", ".join(name.split(": ", 1)[-1] for name in selection.selected_features)
            or "None"
        )
        all_label = ", ".join(name.split(": ", 1)[-1] for name in all_feature_names)

        selected_fits = selected_snapshot.investment <= full_budget
        all_affordable = all_snapshot.investment <= full_budget

        rows: list[tuple[str, ...]] = [
            (
                "ILP selected",
                selected_label,
                "Yes" if selected_fits else "No",
                f"EUR {selected_snapshot.investment:,.0f}",
                f"EUR {selected_snapshot.expected:,.0f}",
                f"{selected_snapshot.roi:.0%}",
                f"EUR {selected_snapshot.var_95:,.0f}",
                f"EUR {selection.selected_proxy_score:,.0f}",
            ),
            (
                "All features option",
                all_label,
                "Yes" if all_affordable else "No",
                f"EUR {all_snapshot.investment:,.0f}",
                f"EUR {all_snapshot.expected:,.0f}",
                f"{all_snapshot.roi:.0%}",
                f"EUR {all_snapshot.var_95:,.0f}",
                f"EUR {selection.all_proxy_score:,.0f}",
            ),
        ]
        headers = (
            "Portfolio Option",
            "Feature Set",
            "Fits 100% Budget",
            "Cost",
            "Expected",
            "Portfolio ROI",
            "BVF 95%",
            "var_floor proxy score",
        )
        return PortfolioComparisonView(rows=rows, headers=headers)

    def _compute_feature_npv(
        self,
        *,
        discount_rate: float | None = None,
        years_list: tuple[int, ...] = (1, 3),
    ) -> dict[str, dict[int, float]]:
        """Compute per-feature NPV using Multi-Year Monte Carlo (same method as NB 03).

        Uses ``FinancialCalculator.result_npv()`` for discounting — the same
        library path as NB 03's ``BlockchainCaseStudyService.npv_rows()``.

        Returns dict mapping feature.name -> {years: npv_value}.
        """
        from fhs.core.model.value_objects.multi_year_result import (
            MultiYearResult,
            YearResult,
        )
        from fhs.core.services.financial import FinancialCalculator
        from fhs.core.services.simulation.simulator import FeatureSimulator

        dr = discount_rate or self._context.discount_rate
        seed = self._context.seed
        n_scenarios = self._context.scenarios
        max_years = max(years_list)

        result: dict[str, dict[int, float]] = {}
        for idx, feature in enumerate(self._context.features):
            sim = FeatureSimulator(seed=seed + idx)
            myr = sim.simulate_feature_multi_year(
                feature, years=max_years, scenarios=n_scenarios, discount_rate=dr
            )

            # Deduct OpEx from each year's scenarios (same as NB 03)
            net_years = [
                YearResult.from_scenarios(
                    year=yr.year,
                    scenarios=yr.scenarios - feature.annual_operating_cost,
                )
                for yr in myr.years
            ]

            npv_by_years: dict[int, float] = {}
            for n_yr in years_list:
                net_myr = MultiYearResult(
                    feature_name=feature.name,
                    years=net_years[:n_yr],
                    discount_rate=dr,
                )
                npv_summary = FinancialCalculator.result_npv(
                    net_myr, feature.development_cost, dr
                )
                npv_by_years[n_yr] = round(npv_summary.expected)

            result[feature.name] = npv_by_years
        return result

    def npv_feature_comparison_rows(
        self,
        *,
        discount_rate: float = 0.08,
    ) -> list[tuple[str, ...]]:
        """Build per-feature NPV comparison rows (Investment, NPV Year 1, NPV 3 Years).

        Uses the same Multi-Year Monte Carlo + cashflow method as NB 03
        (Option A — upfront investment, OpEx deducted per year).
        Returns rows ready for ``show.npv_comparison()``.
        """
        npv_scores = self._compute_feature_npv(
            discount_rate=discount_rate, years_list=(1, 3)
        )

        rows: list[tuple[str, ...]] = []
        for feature in self._context.features:
            scores = npv_scores[feature.name]
            cost = feature.development_cost
            pi = scores[3] / cost if cost > 0 else 0.0
            rows.append(
                (
                    feature.name,
                    f"EUR {cost:,.0f}",
                    f"EUR {scores[1]:,.0f}",
                    f"EUR {scores[3]:,.0f}",
                    f"{pi:.2f}",
                )
            )
        return rows

    def npv_decision_table_rows(
        self,
        budget_levels: dict[str, float],
        ilp_year1: dict[str, OptimizationResult],
        ilp_3year: dict[str, OptimizationResult],
        *,
        discount_rate: float = 0.08,
    ) -> list[tuple[str, ...]]:
        """Build combined NPV decision table rows across budget levels and horizons.

        Uses the same Multi-Year Monte Carlo NPV as NB 03 for portfolio totals.
        Returns rows ready for ``show.npv_decision_table()``.
        """

        def selection_summary(feature_names: list[str]) -> str:
            if not feature_names:
                return "— none —"
            return ", ".join(
                name.split(": ", 1)[-1] if ": " in name else name
                for name in feature_names
            )

        def decision_action(feature_names: list[str], npv_total: float) -> str:
            if not feature_names:
                return "Hold — no positive-NPV portfolio fits budget"
            if npv_total <= 0:
                return "Reassess — negative portfolio NPV"
            if len(feature_names) == len(all_features):
                return "Invest — all features create value"
            return "Invest in selected; backlog rest"

        npv_scores = self._compute_feature_npv(
            discount_rate=discount_rate, years_list=(1, 3)
        )
        all_features = self._context.features

        rows: list[tuple[str, ...]] = []
        for label, budget in budget_levels.items():
            # 3-Year first (primary horizon), Year-1 second (payback check)
            for horizon, results, yr_key in [
                ("3 Years", ilp_3year, 3),
                ("Year 1", ilp_year1, 1),
            ]:
                result = results[label]
                selected = result.recommended_features
                selection_str = selection_summary(selected)
                portfolio_npv = sum(
                    npv_scores[f.name][yr_key]
                    for f in all_features
                    if f.name in selected
                )
                action = decision_action(selected, portfolio_npv)

                rows.append(
                    (
                        label,
                        f"EUR {budget:,.0f}",
                        horizon,
                        selection_str,
                        f"EUR {portfolio_npv:,.0f}",
                        action,
                    )
                )
        return rows


@dataclass(frozen=True)
class PortfolioComparisonView:
    """Result of portfolio_comparison_rows() — rows and headers for show.sensitivity()."""

    rows: list[tuple[str, ...]]
    headers: tuple[str, ...]


@dataclass(frozen=True)
class FeatureSelectionView:
    """Result of feature_selection_view() — rows plus analytics for the rest of the cell."""

    rows: list[tuple[str, ...]]
    headers: tuple[str, ...]
    selected_features: list[str]
    all_proxy_score: float
    selected_proxy_score: float
    has_negative_roi: bool


@dataclass(frozen=True)
class NegativeScoreRowsView:
    """Rows and candidate lists for negative-score notebook analysis."""

    rows: list[tuple[str, ...]]
    positive_features: list[str]
    negative_features: list[str]
