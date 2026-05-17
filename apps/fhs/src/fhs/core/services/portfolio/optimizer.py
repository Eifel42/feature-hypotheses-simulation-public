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
Portfolio Optimizer for Feature Hypotheses Simulation

DEPRECATED: This module is superseded by fhs.application.optimization_service.PortfolioOptimizer.
All new code should use the application layer optimizer.

Extracted from PortfolioAdvisor (§1.1 DDD Refactoring).
Handles combinatorial and greedy feature selection within constraints.
"""  # pragma: no cover - deprecated, superseded by fhs.application.optimization_service.PortfolioOptimizer

import logging
from collections.abc import Callable
from itertools import combinations
from typing import Any, cast

import numpy as np

from ...model import Feature, SimulationResult
from ...model.exceptions import (
    PortfolioOptimizationError,
    ValidationError,
)
from ...model.value_objects import Budget
from ..risk import RiskCalculator, RiskInterpreter
from .utils import aggregate_portfolio_scenarios_from_results

logger = logging.getLogger("fhs.portfolio_optimizer")
SPRINT_LENGTH_WEEKS = 2


class PortfolioOptimizer:  # pragma: no cover - deprecated, use fhs.application.optimization_service.PortfolioOptimizer
    """Optimizes feature portfolio selection under constraints.

    DEPRECATED: Use fhs.application.optimization_service.PortfolioOptimizer instead.

    Provides three optimization strategies:
    - ``optimize_portfolio``: combinatorial (exact) for small feature counts
    - ``optimize_portfolio_by_budget``: greedy selection within a EUR budget
    - ``optimize_portfolio_by_sprint``: greedy selection within a week capacity

    Correlation matrix construction is intentionally handled in
    ``portfolio/correlation.py`` to keep this optimizer focused on selection.
    """

    def __init__(
        self,
        features: list[Feature],
        calculator: RiskCalculator,
        risk_interpreter: RiskInterpreter,
    ):
        self.features = features
        self.calculator = calculator
        self.risk_interpreter = risk_interpreter

    def _risk_ratio(self, expected: float, var_95: float) -> float:
        """Calculate risk ratio using centralized RiskCalculator."""
        return self.calculator.calculate_risk_ratio(expected, var_95, clamp=True)

    def optimize_portfolio(
        self,
        max_features: int,
        simulation_results: dict[str, SimulationResult],
    ) -> dict[str, Any]:
        """Find the optimal subset of features to implement.

        Evaluates all C(n, k) combinations and selects the one that
        maximizes expected business value relative to downside risk.

        Args:
            max_features: Maximum number of features to select
            simulation_results: Pre-computed simulation results

        Returns:
            Dictionary with recommended features, alternatives, and exclusions
        """
        if max_features < 1:
            raise ValidationError(
                "max_features must be at least 1",
                field="max_features",
                value=max_features,
            )
        if max_features >= len(self.features):
            return self._build_optimization_result(
                selected=self.features,
                all_combos=[],
                max_features=len(self.features),
                simulation_results=simulation_results,
            )

        logger.info(
            f"Optimizing portfolio: select {max_features} "
            f"from {len(self.features)} features"
        )

        scored_combos: list[dict[str, Any]] = []
        for combo in combinations(self.features, max_features):
            combo_results = {f.name: simulation_results[f.name] for f in combo}
            portfolio_scenarios = aggregate_portfolio_scenarios_from_results(
                combo_results
            )
            expected = float(np.mean(portfolio_scenarios))
            var_95 = self.calculator.calculate_var(portfolio_scenarios, 0.95)

            scored_combos.append(
                {
                    "features": [f.name for f in combo],
                    "expected_business_value": expected,
                    "var_95_business_value": var_95,
                    "risk_ratio": self._risk_ratio(expected, var_95),
                    "score": var_95,
                }
            )

        scored_combos.sort(key=lambda x: x["score"], reverse=True)

        best = scored_combos[0]
        selected = [self._get_feature_by_name(n) for n in best["features"]]

        return self._build_optimization_result(
            selected=selected,
            all_combos=scored_combos,
            max_features=max_features,
            simulation_results=simulation_results,
        )

    def _greedy_select(
        self,
        features: list[Feature],
        simulation_results: dict[str, SimulationResult],
        *,
        cost_fn: Callable[[Feature], float],  # Feature → float (EUR or weeks)
        budget: float,
        strategy: str = "net_value",
        budget_name: str = "budget",
        _unit: str = "EUR",
    ) -> dict[str, Any]:
        """Generalized greedy selection algorithm.

        Args:
            features: Features to select from
            simulation_results: Pre-computed simulation results
            cost_fn: Function to extract cost from feature (development_cost or development_weeks)
            budget: Total budget available
            strategy: Sorting criterion: "net_value", "risk_adjusted", "var_floor"
            budget_name: Name of budget for logging/output
            unit: Unit name for logging/output

        Returns:
            Dict with selected features, metrics, and alternatives
        """
        feature_metrics: list[dict[str, Any]] = []
        for feature in features:
            result = simulation_results[feature.name]
            net_value = result.net_value
            roi = result.roi
            expected_business_value = result.expected_business_value
            std_dev = float(result.std) * feature.business_value_per_conversion
            business_value_at_risk = result.business_value_at_risk_95
            cost = cost_fn(feature)

            feature_metrics.append(
                {
                    "feature": feature,
                    "name": feature.name,
                    "cost": cost,
                    "expected_business_value": expected_business_value,
                    "net_value": net_value,
                    "roi": roi,
                    "profit_margin": result.profit_margin,
                    "std_dev": std_dev,
                    "business_value_at_risk_95": business_value_at_risk,
                    "sort_net_value": net_value,
                    "sort_risk_adjusted": (
                        net_value / std_dev if std_dev > 0 else net_value
                    ),
                    "sort_var_floor": business_value_at_risk - feature.development_cost,
                }
            )

        sort_key = f"sort_{strategy}"
        feature_metrics.sort(
            key=lambda x: cast(float, x[sort_key]),
            reverse=True,
        )

        selected: list[Feature] = []
        remaining_budget = budget
        total_cost = 0.0

        for metric in feature_metrics:
            cost = cast(float, metric["cost"])
            if cost <= remaining_budget:
                selected.append(cast(Feature, metric["feature"]))
                total_cost += cost
                remaining_budget -= cost

        if not selected:
            logger.warning(
                f"No features fit within {budget_name} {budget}. "
                f"Cheapest feature costs {min(cast(float, m['cost']) for m in feature_metrics)}"
            )
            return {
                "selected": [],
                "total_cost": 0.0,
                "budget": budget,
                "budget_remaining": budget,
                "feature_metrics": feature_metrics,
                "message": f"No features fit within {budget_name} {budget}",
            }

        selected_results = {f.name: simulation_results[f.name] for f in selected}
        portfolio_scenarios = aggregate_portfolio_scenarios_from_results(
            selected_results
        )

        expected_business_value = float(np.mean(portfolio_scenarios))
        var_95 = self.calculator.calculate_var(portfolio_scenarios, 0.95)
        portfolio_net_value = expected_business_value - total_cost
        portfolio_roi = (portfolio_net_value / total_cost) if total_cost > 0 else 0.0

        return {
            "selected": selected,
            "total_cost": total_cost,
            "expected_business_value": expected_business_value,
            "var_95": var_95,
            "net_value": portfolio_net_value,
            "roi": portfolio_roi,
            "risk_ratio": self._risk_ratio(expected_business_value, var_95),
            "budget": budget,
            "budget_remaining": remaining_budget,
            "feature_metrics": feature_metrics,
        }

    @staticmethod
    def _validate_strategy(strategy: str) -> None:
        valid_strategies = ("net_value", "risk_adjusted", "var_floor")
        if strategy not in valid_strategies:
            raise ValidationError(
                f"Unknown strategy '{strategy}'. Valid options: {valid_strategies}",
                field="strategy",
                value=strategy,
            )

    @staticmethod
    def _normalize_budget_input(budget: float | Budget) -> Budget:
        budget_amount = budget.amount if isinstance(budget, Budget) else float(budget)
        if budget_amount < 0:
            raise PortfolioOptimizationError(
                f"Budget must be non-negative. Got {budget_amount}.",
                budget=budget_amount,
                constraint_type="budget",
            )
        if isinstance(budget, Budget):
            return budget
        return Budget(amount=budget_amount, currency="EUR")

    @staticmethod
    def _budget_alternatives(result: dict[str, Any]) -> list[dict[str, Any]]:
        selected_names = {feature.name for feature in result["selected"]}
        alternatives = []
        for metric in result["feature_metrics"]:
            if metric["name"] in selected_names:
                continue
            alternatives.append(
                {
                    "name": metric["name"],
                    "cost": metric["cost"],
                    "expected_business_value": metric["expected_business_value"],
                    "net_value": metric["net_value"],
                    "roi": metric["roi"],
                    "profit_margin": metric["profit_margin"],
                    "reason": (
                        "High ROI but not selected"
                        if metric["roi"] > 0
                        else "Negative ROI"
                    ),
                }
            )
        return alternatives[:5]

    def _build_budget_response(
        self,
        *,
        budget: Budget,
        strategy: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        if not result["selected"]:
            return {
                "recommended_features": [],
                "total_development_cost": 0.0,
                "total_expected_business_value": 0.0,
                "portfolio_net_value": 0.0,
                "portfolio_roi": 0.0,
                "budget": budget.amount,
                "budget_remaining": budget.amount,
                "alternatives": result["feature_metrics"][:5],
                "budget_exceeded": False,
                "message": result.get("message", "No features selected"),
            }

        return {
            "recommended_features": [feature.name for feature in result["selected"]],
            "total_development_cost": result["total_cost"],
            "total_expected_business_value": result["expected_business_value"],
            "portfolio_net_value": result["net_value"],
            "portfolio_roi": result["roi"],
            "portfolio_var_95": result["var_95"],
            "portfolio_risk_ratio": result["risk_ratio"],
            "budget": budget.amount,
            "budget_remaining": result["budget_remaining"],
            "strategy": strategy,
            "alternatives": self._budget_alternatives(result),
            "budget_exceeded": False,
        }

    def _run_budget_selection(
        self,
        *,
        budget: Budget,
        simulation_results: dict[str, SimulationResult],
        strategy: str,
    ) -> dict[str, Any]:
        logger.info(
            f"Optimizing portfolio by budget: {budget.amount} EUR available, "
            f"{len(self.features)} features to select from"
        )
        return self._greedy_select(
            features=self.features,
            simulation_results=simulation_results,
            cost_fn=lambda f: f.development_cost,
            budget=budget.amount,
            strategy=strategy,
            budget_name="budget",
            _unit="EUR",
        )

    @staticmethod
    def _validate_sprint_inputs(
        *,
        capacity_weeks: int,
    ) -> None:
        if capacity_weeks < 1:
            raise ValidationError(
                f"capacity_weeks must be at least 1. Got {capacity_weeks}.",
                field="capacity_weeks",
                value=capacity_weeks,
            )

    def _split_sprint_features(self) -> tuple[list[Feature], list[Feature]]:
        timed = [
            feature
            for feature in self.features
            if feature.development_weeks is not None
        ]
        untimed = [
            feature for feature in self.features if feature.development_weeks is None
        ]
        if untimed:
            logger.warning(
                f"{len(untimed)} feature(s) have no development_weeks and are "
                f"excluded from sprint planning: "
                f"{[feature.name for feature in untimed]}"
            )
        if not timed:
            raise PortfolioOptimizationError(
                "No features have development_weeks set. "
                "Assign development_weeks to each Feature before calling "
                "optimize_portfolio_by_sprint().",
                budget=0,
                constraint_type="development_weeks",
            )
        return timed, untimed

    def _run_sprint_selection(
        self,
        *,
        timed: list[Feature],
        capacity_weeks: int,
        simulation_results: dict[str, SimulationResult],
        strategy: str,
    ) -> dict[str, Any]:
        logger.info(
            f"Sprint optimisation: capacity={capacity_weeks}w, "
            f"sprint={SPRINT_LENGTH_WEEKS}w, strategy='{strategy}', "
            f"{len(timed)} timed features"
        )
        return self._greedy_select(
            features=timed,
            simulation_results=simulation_results,
            cost_fn=lambda f: f.development_weeks or 0.0,
            budget=float(capacity_weeks),
            strategy=strategy,
            budget_name="capacity",
            _unit="weeks",
        )

    def _validated_sprint_selection(
        self,
        *,
        capacity_weeks: int,
        simulation_results: dict[str, SimulationResult],
        strategy: str,
    ) -> tuple[dict[str, Any], list[Feature]]:
        self._validate_strategy(strategy)
        self._validate_sprint_inputs(
            capacity_weeks=capacity_weeks,
        )
        timed, untimed = self._split_sprint_features()
        result = self._run_sprint_selection(
            timed=timed,
            capacity_weeks=capacity_weeks,
            simulation_results=simulation_results,
            strategy=strategy,
        )
        return result, untimed

    @staticmethod
    def _build_sprint_response(
        *,
        capacity_weeks: int,
        strategy: str,
        result: dict[str, Any],
        untimed: list[Feature],
    ) -> dict[str, Any]:
        weeks_used = int(result["total_cost"])
        weeks_remaining = capacity_weeks - weeks_used
        total_sprints = capacity_weeks / SPRINT_LENGTH_WEEKS
        sprints_used = weeks_used / SPRINT_LENGTH_WEEKS
        sprints_remaining = weeks_remaining / SPRINT_LENGTH_WEEKS
        skipped_features = [feature.name for feature in untimed]

        if not result["selected"]:
            return {
                "recommended_features": [],
                "capacity_weeks": capacity_weeks,
                "weeks_used": 0,
                "weeks_remaining": capacity_weeks,
                "sprint_length_weeks": SPRINT_LENGTH_WEEKS,
                "total_sprints": total_sprints,
                "sprints_used": 0.0,
                "sprints_remaining": total_sprints,
                "strategy": strategy,
                "total_expected_business_value": 0.0,
                "portfolio_net_value": 0.0,
                "portfolio_var_95": 0.0,
                "portfolio_risk_ratio": 0.0,
                "portfolio_roi": 0.0,
                "alternatives": result["feature_metrics"][:5],
                "skipped_features": skipped_features,
                "message": result.get("message", "No features selected"),
            }

        selected_names = {feature.name for feature in result["selected"]}
        alternatives = [
            {
                "name": metric["name"],
                "development_weeks": metric["cost"],
                "cost": metric["feature"].development_cost,
                "expected_business_value": metric["expected_business_value"],
                "net_value": metric["net_value"],
            }
            for metric in result["feature_metrics"]
            if metric["name"] not in selected_names
        ]

        return {
            "recommended_features": [feature.name for feature in result["selected"]],
            "capacity_weeks": capacity_weeks,
            "weeks_used": weeks_used,
            "weeks_remaining": weeks_remaining,
            "sprint_length_weeks": SPRINT_LENGTH_WEEKS,
            "total_sprints": total_sprints,
            "sprints_used": sprints_used,
            "sprints_remaining": sprints_remaining,
            "strategy": strategy,
            "total_expected_business_value": result["expected_business_value"],
            "portfolio_net_value": result["net_value"],
            "portfolio_var_95": result["var_95"],
            "portfolio_risk_ratio": result["risk_ratio"],
            "portfolio_roi": result["roi"],
            "alternatives": alternatives[:5],
            "skipped_features": skipped_features,
        }

    def optimize_portfolio_by_budget(
        self,
        budget: float | Budget,
        simulation_results: dict[str, SimulationResult],
        strategy: str = "net_value",
    ) -> dict[str, Any]:
        """Find the optimal subset of features within a budget constraint.

        Uses a greedy algorithm (sorted by the chosen strategy, selected until
        budget exhausted).

        Args:
            budget: Total development budget available (Budget value object or float in EUR)
            simulation_results: Pre-computed simulation results
            strategy: Sorting criterion: "net_value", "risk_adjusted", "var_floor"
        """
        budget = self._normalize_budget_input(budget)
        self._validate_strategy(strategy)
        result = self._run_budget_selection(
            budget=budget,
            simulation_results=simulation_results,
            strategy=strategy,
        )
        return self._build_budget_response(
            budget=budget,
            strategy=strategy,
            result=result,
        )

    def optimize_portfolio_by_sprint(
        self,
        capacity_weeks: int,
        simulation_results: dict[str, SimulationResult],
        strategy: str = "net_value",
    ) -> dict[str, Any]:
        """Find the optimal subset of features within a sprint capacity.

        Uses the same greedy algorithm as ``optimize_portfolio_by_budget``,
        but treats ``Feature.development_weeks`` as the scarce resource.
        """
        result, untimed = self._validated_sprint_selection(
            capacity_weeks=capacity_weeks,
            simulation_results=simulation_results,
            strategy=strategy,
        )
        return self._build_sprint_response(
            capacity_weeks=capacity_weeks,
            strategy=strategy,
            result=result,
            untimed=untimed,
        )

    def _build_optimization_result(
        self,
        selected: list[Feature],
        all_combos: list[dict[str, Any]],
        max_features: int,
        simulation_results: dict[str, SimulationResult],
    ) -> dict[str, Any]:
        """Build the optimization result dictionary."""
        selected_results = {f.name: simulation_results[f.name] for f in selected}
        portfolio_scenarios = aggregate_portfolio_scenarios_from_results(
            selected_results
        )

        expected = float(np.mean(portfolio_scenarios))
        var_95 = self.calculator.calculate_var(portfolio_scenarios, 0.95)

        selected_names = {f.name for f in selected}
        excluded = []
        for feature in self.features:
            if feature.name not in selected_names:
                result = simulation_results[feature.name]
                bv = feature.business_value_per_conversion
                exp_bv = result.expected_value * bv
                var_bv = result.var_95 * bv
                rr = self._risk_ratio(exp_bv, var_bv)
                excluded.append(
                    {
                        "name": feature.name,
                        "expected_business_value": exp_bv,
                        "risk_ratio": rr,
                        "reason": self._exclusion_reason(feature, rr, selected),
                    }
                )

        alternatives = all_combos[1:4] if len(all_combos) > 1 else []

        return {
            "recommended_features": [f.name for f in selected],
            "total_expected_business_value": expected,
            "portfolio_var_95": var_95,
            "portfolio_risk_ratio": self._risk_ratio(expected, var_95),
            "max_features": max_features,
            "alternatives": alternatives,
            "excluded_features": excluded,
        }

    @staticmethod
    def _exclusion_reason(
        feature: Feature, risk_ratio: float, selected: list[Feature]
    ) -> str:
        """Generate a human-readable reason why a feature was excluded."""
        if risk_ratio > 0.4:
            return f"High risk ratio ({risk_ratio:.2f})"
        bv = feature.business_value_per_conversion
        exp = feature.expected_users * feature.conversion_rate * bv
        for sel in selected:
            sel_bv = sel.business_value_per_conversion
            sel_exp = sel.expected_users * sel.conversion_rate * sel_bv
            if sel_exp > exp and sel.uncertainty <= feature.uncertainty:
                return f"Better alternative: {sel.name}"
        return "Lower total contribution to portfolio"

    def _get_feature_by_name(self, name: str) -> Feature:
        """Look up a feature by name."""
        for f in self.features:
            if f.name == name:
                return f
        raise ValidationError(
            f"Feature '{name}' not found",
            field="name",
            value=name,
        )
