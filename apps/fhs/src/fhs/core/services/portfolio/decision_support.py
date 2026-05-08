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

"""Portfolio decision-support service for rankings, guardrails, and tables."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

import numpy as np

from fhs.core.model import (
    BudgetRiskRow,
    Feature,
    FeatureRanking,
    NegativeScoreComparisonRow,
    NegativeScoreFeature,
    NegativeScoreReport,
    OptimizationResult,
    SimulationResult,
    StrategyCategoryCostRow,
)
from fhs.core.services.risk.calculator import RiskCalculator


class PortfolioDecisionSupportService:
    """Build typed decision-support outputs from precomputed portfolio inputs."""

    @staticmethod
    def feature_key(feature: Feature) -> str:
        return getattr(feature, "key", feature.name.split(":")[0].strip())

    @staticmethod
    def feature_overview_rows(
        *,
        features: Sequence[Feature],
        simulation_results: Mapping[str, SimulationResult],
    ) -> list[tuple[str, ...]]:
        """Rows for feature-level overview table."""
        rows: list[tuple[str, ...]] = []
        for feature in sorted(features, key=lambda item: item.name):
            result = simulation_results[feature.name]
            expected = result.expected_business_value
            var_95 = result.business_value_at_risk_95
            risk_adjusted_roi = (
                var_95 / float(feature.development_cost)
                if float(feature.development_cost) > 0
                else float("inf")
            )
            llp = feature.likelihood_of_non_delivery
            if llp <= 0.15:
                zone = "Low"
            elif llp <= 0.30:
                zone = "Medium"
            else:
                zone = "High"
            roi_display = (
                "inf" if np.isinf(risk_adjusted_roi) else f"{risk_adjusted_roi:.2f}x"
            )
            rows.append(
                (
                    PortfolioDecisionSupportService.feature_key(feature),
                    feature.name,
                    f"EUR {feature.development_cost:,.0f}",
                    f"EUR {expected:,.0f}",
                    f"EUR {var_95:,.0f}",
                    roi_display,
                    f"{llp:.0%}",
                    zone,
                )
            )
        return rows

    @staticmethod
    def llp_rows(
        *,
        features: Sequence[Feature],
        simulation_results: Mapping[str, SimulationResult],
    ) -> list[tuple[str, ...]]:
        """Rows with LLP and delivery-adjusted risk exposure."""
        rows: list[tuple[str, ...]] = []
        for feature in sorted(features, key=lambda item: item.name):
            result = simulation_results[feature.name]
            expected = result.expected_business_value
            llp = feature.likelihood_of_non_delivery
            at_risk = expected * llp
            rows.append(
                (
                    feature.name,
                    f"{llp:.0%}",
                    f"EUR {expected:,.0f}",
                    f"EUR {at_risk:,.0f}",
                    feature.dependency_cluster or "Independent",
                )
            )
        return rows

    @staticmethod
    def empty_solver_result(budget: float, reason: str) -> OptimizationResult:
        """Typed placeholder result for non-optimizable budget levels."""
        return OptimizationResult(
            recommended_features=(),
            total_cost=0.0,
            portfolio_expected=0.0,
            portfolio_var_95=0.0,
            portfolio_cvar_95=0.0,
            portfolio_std_dev=0.0,
            budget=float(budget),
            budget_remaining=float(budget),
            computation_time_sec=0.0,
            combinations_evaluated=0,
            solver="not_run",
            strategy="var_floor",
            portfolio_roi=0.0,
            roi=0.0,
            safety_buffer=0.0,
            message=reason,
            metadata={"status": "skipped", "reason": reason},
        )

    @staticmethod
    def feature_score_analysis(
        *,
        features: Sequence[Feature],
        simulation_results: Mapping[str, SimulationResult],
    ) -> dict[str, float]:
        """Per-feature var_floor proxy score used by ILP baseline screening."""
        return {
            feature.name: (
                float(simulation_results[feature.name].business_value_at_risk_95)
                - float(feature.development_cost)
            )
            for feature in features
        }

    @staticmethod
    def optimize_budget_levels_with_guardrails(
        *,
        budget_levels: Mapping[str, float],
        features: Sequence[Feature],
        simulation_results: Mapping[str, SimulationResult],
        optimize_for_budget: Callable[[float], OptimizationResult],
    ) -> dict[str, OptimizationResult]:
        """Run optimization across budget levels with screening guardrails."""
        min_feature_cost = min(float(feature.development_cost) for feature in features)
        feature_proxy_score = PortfolioDecisionSupportService.feature_score_analysis(
            features=features,
            simulation_results=simulation_results,
        )

        results: dict[str, OptimizationResult] = {}
        for label, budget in budget_levels.items():
            budget_value = float(budget)
            affordable_positive = [
                feature
                for feature in features
                if float(feature.development_cost) <= budget_value
                and feature_proxy_score.get(feature.name, 0.0) > 0.0
            ]

            if budget_value < min_feature_cost:
                results[label] = PortfolioDecisionSupportService.empty_solver_result(
                    budget_value,
                    (
                        "Not optimized: budget < cheapest feature "
                        f"(EUR {min_feature_cost:,.0f})"
                    ),
                )
                continue

            if not affordable_positive:  # pragma: no cover - defensive
                results[label] = (
                    PortfolioDecisionSupportService.empty_solver_result(  # pragma: no cover - defensive
                        budget_value,  # pragma: no cover - defensive
                        (  # pragma: no cover - defensive
                            "Not optimized: no feature with positive var_floor score "  # pragma: no cover - defensive
                            "under this budget"  # pragma: no cover - defensive
                        ),  # pragma: no cover - defensive
                    )
                )  # pragma: no cover - defensive
                continue  # pragma: no cover - defensive
            # pragma: no cover - defensive
            results[label] = optimize_for_budget(
                budget_value
            )  # pragma: no cover - defensive

        return results

    @staticmethod
    def budget_sensitivity(
        *,
        levels: Mapping[str, float],
        features: Sequence[Feature],
        simulation_results: Mapping[str, SimulationResult],
        optimize_for_budget: Callable[[float], OptimizationResult],
    ) -> dict[str, OptimizationResult]:
        """Run optimization over labeled budget levels with guard-rails."""
        if not levels:
            return {}  # pragma: no cover - defensive

        min_feature_cost = min(float(feature.development_cost) for feature in features)
        proxy_scores = PortfolioDecisionSupportService.feature_score_analysis(
            features=features,
            simulation_results=simulation_results,
        )

        results: dict[str, OptimizationResult] = {}
        for label, budget in levels.items():
            budget_value = float(budget)

            affordable_positive = [
                feature
                for feature in features
                if float(feature.development_cost) <= budget_value
                and proxy_scores.get(feature.name, 0.0) > 0.0
            ]

            if budget_value < min_feature_cost:
                reason = (
                    f"Not optimized: budget < cheapest feature "
                    f"(EUR {min_feature_cost:,.0f}); build remains in backlog"
                )
                results[label] = PortfolioDecisionSupportService.empty_solver_result(
                    budget_value,
                    reason,
                )
                continue

            if not affordable_positive:
                reason = (  # pragma: no cover - defensive
                    "Not optimized: no feature with positive var_floor score "  # pragma: no cover - defensive
                    "under this budget; build remains in backlog"  # pragma: no cover - defensive
                )  # pragma: no cover - defensive
                results[label] = (
                    PortfolioDecisionSupportService.empty_solver_result(  # pragma: no cover - defensive
                        budget_value,  # pragma: no cover - defensive
                        reason,  # pragma: no cover - defensive
                    )
                )  # pragma: no cover - defensive
                continue  # pragma: no cover - defensive

            results[label] = optimize_for_budget(budget_value)

        return results

    @staticmethod
    def rank_features(
        *,
        features: Sequence[Feature],
        simulation_results: Mapping[str, SimulationResult],
        strategy: str = "var_floor",
    ) -> list[FeatureRanking]:
        """Rank features by selected strategy using risk-adjusted profile metrics."""
        if strategy not in {"var_floor", "risk_ratio", "rorac", "risk_adjusted_roi"}:
            raise ValueError(
                "Unknown ranking strategy. Expected one of: "
                "var_floor, risk_ratio, rorac, risk_adjusted_roi"
            )

        rows: list[FeatureRanking] = []
        for feature in features:
            result = simulation_results[feature.name]
            scenarios = np.asarray(result.results, dtype=float) * float(
                result.business_value_per_conversion
            )
            profile = RiskCalculator.feature_ranking_metrics(
                feature_name=feature.name,
                bv_scenarios=scenarios,
                development_cost=float(feature.development_cost),
            )
            rows.append(
                FeatureRanking(
                    feature=feature.name,
                    expected_business_value=profile.expected_bv,
                    var_95_business_value=profile.bv_var,
                    risk_ratio=profile.risk_ratio,
                    llp=float(feature.likelihood_of_non_delivery),
                    cost=float(feature.development_cost),
                    bv_cvar_business_value=profile.bv_cvar,
                    loss_var=profile.loss_var,
                    loss_cvar=profile.loss_cvar,
                    rorac=profile.rorac,
                    risk_adjusted_roi=profile.risk_adjusted_roi,
                    confidence_level=profile.confidence_level,
                )
            )

        sort_key = {
            "var_floor": lambda row: (-row.var_95_business_value, row.feature),
            "risk_ratio": lambda row: (row.risk_ratio, row.feature),
            "rorac": lambda row: (-row.rorac, row.feature),
            "risk_adjusted_roi": lambda row: (-row.risk_adjusted_roi, row.feature),
        }[strategy]

        return sorted(rows, key=sort_key)

    @staticmethod
    def negative_score_analysis(
        *,
        features: Sequence[Feature],
        simulation_results: Mapping[str, SimulationResult],
        solve_candidates: Callable[
            [tuple[str, ...] | None], Mapping[str, OptimizationResult]
        ],
    ) -> NegativeScoreReport:
        """Analyze ILP behavior for negative individual var_floor scores."""
        scores: list[NegativeScoreFeature] = []
        positive_features: list[str] = []
        negative_features: list[str] = []
        for feature in features:
            var_95 = float(simulation_results[feature.name].business_value_at_risk_95)
            score = var_95 - float(feature.development_cost)
            has_positive_score = score >= 0.0
            scores.append(
                NegativeScoreFeature(
                    feature=feature.name,
                    cost=float(feature.development_cost),
                    var_95_business_value=var_95,
                    var_floor_score=score,
                    ilp_considers=has_positive_score,
                )
            )
            if has_positive_score:
                positive_features.append(feature.name)
            else:
                negative_features.append(feature.name)

        results_all = solve_candidates(None)

        if positive_features and len(positive_features) != len(features):
            results_positive = solve_candidates(tuple(positive_features))
        else:
            results_positive = results_all

        comparisons: list[NegativeScoreComparisonRow] = []
        for candidate_label, result_set in (
            ("All features", results_all),
            ("Positive-score only", results_positive),
        ):
            for solver in ("exact", "ilp"):
                row = result_set[solver]
                comparisons.append(
                    NegativeScoreComparisonRow(
                        candidate_set=candidate_label,
                        solver=solver.upper(),
                        selected_features=tuple(row.recommended_features),
                        selected_count=len(row.recommended_features),
                        portfolio_var_95=row.portfolio_var_95,
                        total_cost=row.total_cost,
                    )
                )

        gap = (
            results_all["exact"].portfolio_var_95 - results_all["ilp"].portfolio_var_95
        )

        return NegativeScoreReport(
            scores=tuple(sorted(scores, key=lambda s: s.var_floor_score)),
            positive_features=tuple(sorted(positive_features)),
            negative_features=tuple(sorted(negative_features)),
            comparisons=tuple(comparisons),
            all_features_exact=results_all["exact"],
            all_features_ilp=results_all["ilp"],
            positive_only_exact=results_positive["exact"],
            positive_only_ilp=results_positive["ilp"],
            gap_exact_minus_ilp=gap,
            ilp_matches_exact=abs(gap) <= 1.0,
        )

    @staticmethod
    def strategy_category_cost_share(
        *,
        selected_names: Iterable[str],
        feature_by_name: Mapping[str, Feature],
        strategy: Mapping[str, Any],
    ) -> tuple[StrategyCategoryCostRow, ...]:
        """Aggregate cost share by strategy category for selected features."""
        category_cost: dict[str, float] = {}
        total_cost = 0.0
        for name in selected_names:
            if name not in feature_by_name:
                continue
            category = str(strategy.get(name, {}).get("category", "Unmapped"))
            cost = float(feature_by_name[name].development_cost)
            category_cost[category] = category_cost.get(category, 0.0) + cost
            total_cost += cost

        rows = [
            StrategyCategoryCostRow(
                category=category,
                cost=cost,
                share=(cost / total_cost) if total_cost > 0 else 0.0,
            )
            for category, cost in sorted(
                category_cost.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ]
        return tuple(rows)

    @staticmethod
    def budget_risk_path(
        *,
        levels: Mapping[str, float],
        optimize_for_budget: Callable[[float], OptimizationResult],
        analyze_delivery_risk: Callable[..., Mapping[str, Any]],
        seed: int = 42,
        systematic_shock_probability: float = 0.05,
        systematic_shock_multiplier: float = 0.30,
    ) -> list[BudgetRiskRow]:
        """Budget-path floors and qualitative risk class across levels."""
        rows: list[BudgetRiskRow] = []
        for label, budget in levels.items():
            result = optimize_for_budget(float(budget))

            delivery = analyze_delivery_risk(result, seed=seed)
            shock = analyze_delivery_risk(
                result,
                seed=seed,
                systematic_shock_probability=systematic_shock_probability,
                systematic_shock_multiplier=systematic_shock_multiplier,
            )

            investment = float(result.total_cost)
            l1_floor = float(delivery.get("market_var_95", 0.0))
            l2_floor = float(delivery.get("simulated_var_95", 0.0))
            l3_floor = float(shock.get("shocked_var_95", 0.0))
            safety_buffer = float(
                shock.get("shocked_safety_buffer", l3_floor - investment)
            )

            if investment <= 0:
                risk_class = "No selection"
            elif safety_buffer >= 0:
                risk_class = "Low" if l3_floor >= 1.2 * investment else "Medium"
            else:
                risk_class = "High"

            rows.append(
                BudgetRiskRow(
                    label=str(label),
                    budget=float(budget),
                    selected_count=len(result.recommended_features),
                    investment=investment,
                    l1_floor=l1_floor,
                    l2_floor=l2_floor,
                    l3_floor=l3_floor,
                    l3_safety_buffer=safety_buffer,
                    risk_class=risk_class,
                )
            )

        return rows

    @staticmethod
    def risk_contribution_rows(
        *,
        names: Iterable[str],
        feature_by_name: Mapping[str, Feature],
        simulation_results: Mapping[str, SimulationResult],
        portfolio_scenarios: np.ndarray,
    ) -> list[tuple[str, float, float, float, float, float]]:
        """Rows for risk contribution table."""
        resolved = list(names)
        if not resolved:
            return []  # pragma: no cover - defensive

        expected = {
            name: simulation_results[name].expected_business_value for name in resolved
        }
        total_expected = float(sum(expected.values()))
        weights = {
            name: (value / total_expected if total_expected > 0 else 0.0)
            for name, value in expected.items()
        }

        portfolio_std = float(np.std(portfolio_scenarios))

        rows: list[tuple[str, float, float, float, float, float]] = []
        for name in resolved:
            feature = feature_by_name[name]
            result = simulation_results[name]
            business_value_array = (
                result.results_array * feature.business_value_per_conversion
            )
            expected_business_value = float(np.mean(business_value_array))
            volatility = float(np.std(business_value_array))
            risk_ratio = (
                (volatility / expected_business_value * 100)
                if expected_business_value > 0
                else 0.0
            )
            contribution = (
                weights[name] * volatility / portfolio_std * 100
                if portfolio_std > 0
                else 0.0
            )
            rows.append(
                (
                    feature.name,
                    weights[name],
                    expected_business_value,
                    volatility,
                    risk_ratio,
                    contribution,
                )
            )

        rows.sort(key=lambda row: row[5], reverse=True)
        return rows
