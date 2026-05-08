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
Integer Linear Programming (ILP) Portfolio Solver

Uses scipy.optimize.milp for mathematical optimization.
Formulates feature selection as a 0/1 knapsack problem.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from fhs.core.model import Feature, SimulationResult
from fhs.core.model.value_objects import Budget, OptimizationStrategy
from fhs.core.services import RiskCalculator
from fhs.core.services.optimization.domain import PortfolioResult
from fhs.core.services.optimization.scoring import (
    ObjectiveFunctionFactory,
    PortfolioMetricsCalculator,
)

logger = logging.getLogger("fhs.optimizer.ilp")


class ILPSolver:
    """
    ILP solver using scipy.optimize.milp.

        Formulates feature selection as integer linear programming:
    - Decision variable: x_i ∈ {0, 1} per feature (build or skip)
    - Budget constraint: Σ(cost_i × x_i) ≤ budget
        - Objective: maximize an additive per-feature proxy score

        Important linearity assumption:
        - ILP can optimize only linear/additive objectives in x_i.
        - For `var_floor` and `sharpe`, the per-feature score is an approximation.
            True portfolio objective values are non-linear because of scenario
            aggregation and correlation effects.
        - The selected portfolio is therefore always re-evaluated with full
            Monte Carlo scenarios after optimization.

    After solving, evaluates selected portfolio with full Monte Carlo simulation
    to account for correlation effects.

    Complexity: O(2^n) worst-case, but branch-and-bound pruning makes it practical
    Recommended for n ≤ 30 features.
    """

    def __init__(self, risk_calculator: RiskCalculator):
        """
        Initialize ILP solver.

        Args:
            risk_calculator: RiskCalculator for VaR/CVaR computation
        """
        self.metrics_calc = PortfolioMetricsCalculator(risk_calculator)

    @property
    def name(self) -> str:
        return "ilp"

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
        Find portfolio via integer linear programming.

        Args:
            features: List of Feature objects to select from
            simulation_results: Mapping of feature name to SimulationResult
            budget: Maximum development budget
            strategy: Optimization criterion (var_floor, expected, sharpe)
                Note: `expected` is additive and directly aligned with ILP.
                `var_floor` and `sharpe` use linear proxy coefficients.
            sum_portfolio_scenarios_fn: Portfolio aggregation callback
            **kwargs: Ignored (for protocol compatibility)

        Returns:
            PortfolioResult with ILP-selected features and post-hoc full
            simulation metrics.
        """
        start_time = time.time()

        # Normalize inputs
        budget_amount = self._normalize_budget(budget)
        discount_rate = float(kwargs.get("discount_rate", 0.08))
        objective_fn = ObjectiveFunctionFactory.create(
            strategy,
            discount_rate=discount_rate,
        )

        n = len(features)
        logger.info(
            f"ILP solver: {n} features, "
            f"budget={budget_amount:.0f}, strategy={objective_fn.name}"
        )

        # Build ILP formulation using NumPy vectorization
        costs, obj_coeffs = self._build_ilp_formulation(
            features, simulation_results, objective_fn
        )

        # Solve ILP
        ilp_result = self._solve_ilp(costs, obj_coeffs, budget_amount, n)

        if not ilp_result.success:
            elapsed = time.time() - start_time  # pragma: no cover - defensive
            logger.warning(
                f"ILP solver failed: {ilp_result.message}"
            )  # pragma: no cover - defensive
            return self._failure_result(  # pragma: no cover - defensive
                budget_amount, objective_fn.name, elapsed, ilp_result.message
            )

        # Extract selected features
        selected_features = self._extract_selected_features(features, ilp_result.x)

        if not selected_features:
            elapsed = time.time() - start_time  # pragma: no cover - defensive
            logger.warning("ILP selected no features")  # pragma: no cover - defensive
            return self._empty_result(
                budget_amount, objective_fn.name, elapsed
            )  # pragma: no cover - defensive

        # Evaluate selected portfolio with full simulation
        combo_results = {f.name: simulation_results[f.name] for f in selected_features}

        if sum_portfolio_scenarios_fn:
            portfolio_scenarios = sum_portfolio_scenarios_fn(combo_results)
        else:
            portfolio_scenarios = self._simple_sum_scenarios(
                selected_features, combo_results
            )

        metrics = self.metrics_calc.calculate(portfolio_scenarios)

        total_cost = sum(f.development_cost for f in selected_features)
        elapsed = time.time() - start_time

        logger.info(
            f"ILP solver completed in {elapsed:.4f}s, "
            f"selected {len(selected_features)} features"
        )

        return PortfolioResult(
            recommended_features=[f.name for f in selected_features],
            total_cost=total_cost,
            portfolio_expected=metrics.expected,
            portfolio_var_95=metrics.var_95,
            portfolio_cvar_95=metrics.cvar_95,
            portfolio_std_dev=metrics.std_dev,
            budget=budget_amount,
            budget_remaining=budget_amount - total_cost,
            computation_time_sec=elapsed,
            combinations_evaluated=1,
            solver=self.name,
            strategy=objective_fn.name,
            metadata={
                "ilp_status": ilp_result.status,
                "ilp_message": ilp_result.message,
            },
        )

    @staticmethod
    def _build_ilp_formulation(
        features: list[Feature],
        simulation_results: dict[str, SimulationResult],
        objective_fn,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Build ILP objective coefficients using NumPy vectorization.

        Args:
            features: List of features
            simulation_results: Simulation results dict
            objective_fn: Objective function

        Returns:
            Tuple of (costs_array, objective_coefficients_array)
        """
        n = len(features)
        costs = np.empty(n)
        obj = np.empty(n)

        for i, feature in enumerate(features):
            result = simulation_results[feature.name]
            costs[i] = feature.development_cost
            obj[i] = objective_fn.score_feature(feature, result)

        return costs, obj

    @staticmethod
    def _solve_ilp(
        costs: np.ndarray,
        obj_coeffs: np.ndarray,
        budget: float,
        n: int,
    ):
        """
        Solve ILP using scipy.optimize.milp.

        Args:
            costs: Cost array (n,)
            obj_coeffs: Objective coefficient array (n,)
            budget: Budget constraint
            n: Number of features

        Returns:
            OptimizeResult from milp
        """
        # milp minimizes → negate to maximize
        c = -obj_coeffs

        # Budget constraint: Σ cost_i × x_i ≤ budget
        budget_constraint = LinearConstraint(
            costs.reshape(1, -1), lb=-np.inf, ub=budget
        )

        # Binary integrality: x_i ∈ {0, 1}
        integrality = np.ones(n, dtype=int)
        variable_bounds = Bounds(lb=np.zeros(n), ub=np.ones(n))

        # Solve
        return milp(
            c=c,
            constraints=budget_constraint,
            integrality=integrality,
            bounds=variable_bounds,
        )

    @staticmethod
    def _extract_selected_features(
        features: list[Feature], solution: np.ndarray
    ) -> list[Feature]:
        """
        Extract selected features from ILP solution.

        Args:
            features: List of all features
            solution: ILP solution array (binary values)

        Returns:
            List of selected features
        """
        selected_indices = np.nonzero(solution > 0.5)[0]
        return [features[i] for i in selected_indices]

    @staticmethod
    # noinspection PyTypeHintsInspection
    def _simple_sum_scenarios(
        selected: list[Feature], combo_results: dict[str, SimulationResult]
    ) -> np.ndarray:
        """Simple portfolio aggregation (vectorized)."""
        arrays = [
            combo_results[f.name].results_array * f.business_value_per_conversion
            for f in selected
        ]
        return np.asarray(np.sum(arrays, axis=0), dtype=float)

    @staticmethod
    # noinspection PyTypeHintsInspection
    def _normalize_budget(budget: float | Budget) -> float:
        """Normalize budget to float."""
        return budget.amount if isinstance(budget, Budget) else budget

    def _empty_result(
        self, budget: float, strategy: str, elapsed: float
    ) -> PortfolioResult:
        """Create empty result when ILP selects nothing."""
        return PortfolioResult(  # pragma: no cover - defensive
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
            message="ILP selected no features",
        )

    def _failure_result(
        self, budget: float, strategy: str, elapsed: float, error_msg: str
    ) -> PortfolioResult:
        """Create failure result when ILP fails."""
        return PortfolioResult(  # pragma: no cover - defensive
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
            message=f"ILP solver failed: {error_msg}",
        )
