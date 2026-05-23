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
Exact Portfolio Solver (Exhaustive Search)

Guarantees global optimum by evaluating all valid feature combinations.
Suitable for small portfolios (≤15 features).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from itertools import combinations
from typing import Any

import numpy as np

from fhs.core.model import Feature, SimulationResult
from fhs.core.model.value_objects import Budget, OptimizationStrategy
from fhs.core.services import RiskCalculator
from fhs.core.services.optimization.domain import PortfolioResult
from fhs.core.services.optimization.scoring import (
    ObjectiveFunctionFactory,
    PortfolioMetricsCalculator,
)
from fhs.core.typing_utils import to_float_array

logger = logging.getLogger("fhs.optimizer.exact")


class ExactSolver:
    """
    Exact solver using exhaustive combinatorial search.

    Evaluates all C(n,k) combinations that fit within budget and selects
    the one that maximizes the chosen metric while accounting for
    portfolio correlation effects.

    Complexity: O(2^n × m) where n=features, m=scenarios
    Recommended for n ≤ 15 features.
    """

    def __init__(self, risk_calculator: RiskCalculator):
        """
        Initialize exact solver.

        Args:
            risk_calculator: RiskCalculator for VaR/CVaR computation
        """
        self.metrics_calc = PortfolioMetricsCalculator(risk_calculator)

    @property
    def name(self) -> str:
        return "exact"

    # noinspection PyTypeHintsInspection
    def optimize(
        self,
        features: list[Feature],
        simulation_results: dict[str, SimulationResult],
        budget: float | Budget,
        strategy: str | OptimizationStrategy,
        sum_portfolio_scenarios_fn: (
            Callable[[dict[str, SimulationResult]], np.ndarray] | None
        ) = None,
        **kwargs,
    ) -> PortfolioResult:
        """
        Find globally optimal portfolio via exhaustive search.

        Args:
            features: List of Feature objects to select from
            simulation_results: Mapping of feature name to SimulationResult
            budget: Maximum development budget
            strategy: Optimization criterion (var_floor, expected, sharpe)
            sum_portfolio_scenarios_fn: Portfolio aggregation callback
            **kwargs: Ignored (for protocol compatibility)

        Returns:
            PortfolioResult with globally optimal feature selection
        """
        start_time = time.time()

        # Normalize inputs
        budget_amount = self._normalize_budget(budget)
        discount_rate = float(kwargs.get("discount_rate", 0.08))
        objective_fn = ObjectiveFunctionFactory.create(
            strategy,
            discount_rate=discount_rate,
        )

        logger.info(
            f"Exact solver: {len(features)} features, "
            f"budget={budget_amount:.0f}, strategy={objective_fn.name}"
        )

        # Generate all budget-feasible combinations using NumPy vectorization
        valid_combos = self._generate_valid_combinations(features, budget_amount)

        if not valid_combos:
            elapsed = time.time() - start_time
            min_cost = min(f.development_cost for f in features)
            logger.warning(
                f"No features fit within budget {budget_amount:.0f}. "
                f"Cheapest feature costs {min_cost:.0f}"
            )
            return self._empty_result(
                budget_amount, objective_fn.name, elapsed, min_cost
            )

        logger.info(f"Evaluating {len(valid_combos)} valid combinations")

        # Evaluate all combinations using vectorized operations
        best_combo, best_metrics = self._find_best_combination(
            valid_combos,
            simulation_results,
            objective_fn,
            sum_portfolio_scenarios_fn,
        )

        elapsed = time.time() - start_time
        total_cost = sum(f.development_cost for f in best_combo)

        logger.info(
            f"Exact solver completed in {elapsed:.3f}s, "
            f"evaluated {len(valid_combos)} combinations, "
            f"selected {len(best_combo)} features"
        )

        return PortfolioResult(
            recommended_features=[f.name for f in best_combo],
            total_cost=total_cost,
            portfolio_expected=best_metrics.expected,  # type: ignore[attr-defined]
            portfolio_var_95=best_metrics.var_95,  # type: ignore[attr-defined]
            portfolio_cvar_95=best_metrics.cvar_95,  # type: ignore[attr-defined]
            portfolio_std_dev=best_metrics.std_dev,  # type: ignore[attr-defined]
            budget=budget_amount,
            budget_remaining=budget_amount - total_cost,
            computation_time_sec=elapsed,
            combinations_evaluated=len(valid_combos),
            solver=self.name,
            strategy=objective_fn.name,
        )

    @staticmethod
    def _generate_valid_combinations(
        features: list[Feature], budget: float
    ) -> list[tuple[Feature, ...]]:
        """
        Generate all budget-feasible feature combinations.

        Uses NumPy vectorization for fast cost checking.

        Args:
            features: List of features
            budget: Budget constraint

        Returns:
            List of valid feature combinations (tuples)
        """
        # Extract costs as NumPy array for vectorized operations
        costs = np.array([f.development_cost for f in features])

        valid_combos = []
        for r in range(1, len(features) + 1):
            for combo in combinations(range(len(features)), r):
                # Vectorized cost sum
                combo_cost = costs[list(combo)].sum()
                if combo_cost <= budget:
                    valid_combos.append(tuple(features[i] for i in combo))

        return valid_combos

    def _find_best_combination(
        self,
        combinations_list: list[tuple[Feature, ...]],
        simulation_results: dict[str, SimulationResult],
        objective_fn,
        sum_portfolio_scenarios_fn,
    ) -> tuple[tuple[Feature, ...], Any]:
        """
        Find combination with highest score.

        Args:
            combinations_list: List of valid combinations
            simulation_results: Simulation results dict
            objective_fn: Objective function for scoring
            sum_portfolio_scenarios_fn: Portfolio aggregation function

        Returns:
            Tuple of (best_combo, best_metrics)
        """
        best_score = -np.inf
        best_combo = None
        best_metrics = None

        for combo in combinations_list:
            combo_results = {f.name: simulation_results[f.name] for f in combo}

            # Aggregate portfolio scenarios (with correlation if provided)
            if sum_portfolio_scenarios_fn:
                portfolio_scenarios = sum_portfolio_scenarios_fn(combo_results)
            else:
                portfolio_scenarios = self._simple_sum_scenarios(combo, combo_results)

            # Calculate metrics using shared calculator
            metrics = self.metrics_calc.calculate(portfolio_scenarios)

            # Score using strategy pattern
            score = objective_fn.score_portfolio(metrics)

            if score > best_score:
                best_score = score
                best_combo = combo
                best_metrics = metrics

        assert best_combo is not None
        assert best_metrics is not None
        return best_combo, best_metrics

    @staticmethod
    # noinspection PyTypeHintsInspection
    def _simple_sum_scenarios(
        combo: tuple[Feature, ...], combo_results: dict[str, SimulationResult]
    ) -> np.ndarray:
        """
        Simple portfolio aggregation (assumes independence).

        Uses NumPy vectorization for fast array summation.

        Args:
            combo: Feature tuple
            combo_results: Simulation results for combo features

        Returns:
            Portfolio scenario array
        """
        # Vectorized array summation
        arrays = [
            combo_results[f.name].results_array * f.business_value_per_conversion
            for f in combo
        ]
        return to_float_array(np.sum(arrays, axis=0))

    @staticmethod
    # noinspection PyTypeHintsInspection
    def _normalize_budget(budget: float | Budget) -> float:
        """Normalize budget to float."""
        return budget.amount if isinstance(budget, Budget) else budget

    def _empty_result(
        self, budget: float, strategy: str, elapsed: float, min_cost: float
    ) -> PortfolioResult:
        """Create empty result for infeasible problem."""
        return PortfolioResult(
            recommended_features=[],
            total_cost=0.0,
            portfolio_expected=0.0,
            portfolio_var_95=0.0,
            portfolio_cvar_95=0.0,
            portfolio_std_dev=0.0,
            budget=budget,
            budget_remaining=budget,
            computation_time_sec=elapsed,
            combinations_evaluated=0,
            solver=self.name,
            strategy=strategy,
            message=f"No features fit within budget {budget:.0f}. "
            f"Cheapest feature costs {min_cost:.0f}",
        )
